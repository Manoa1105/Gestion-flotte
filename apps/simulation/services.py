"""
=============================================================================
Services du moteur de simulation
=============================================================================
Coeur du simulateur :
  - avancer_mission(mission, minutes)  : fait avancer une mission de N minutes
  - calculer_position_gps(mission, km) : interpolation GPS le long du trajet
  - tirer_evenements(mission, ...)     : tirage aleatoire d'evenements
  - terminer_mission_simulee(...)      : fin de mission + creation depense carburant

Appele par la commande management "simulation_run" toutes les secondes.
=============================================================================
"""

import random
from decimal import Decimal
from django.db import transaction
from django.utils import timezone

from apps.missions.models import Mission, PositionGPS
from apps.missions.services import calculer_trajet
from .models import TypeEvenement, EvenementMission


# Prix moyen du gazole a Madagascar (Ariary par litre, mai 2026)
PRIX_GAZOLE_MGA_LITRE = 5500


# =============================================================================
# CALCUL DE POSITION GPS PAR INTERPOLATION
# =============================================================================
def _distance_haversine_km(lat1, lon1, lat2, lon2):
    """Distance entre 2 points GPS en km (formule haversine)."""
    import math
    R = 6371.0  # Rayon Terre en km
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    return 2 * R * math.asin(math.sqrt(a))


def _interpoler_le_long_polyline(polyline_latlon, distance_cible_km):
    """
    Interpole le long d'une suite de points GPS pour trouver la position
    apres avoir parcouru distance_cible_km depuis le debut.

    Args:
        polyline_latlon  : liste de tuples (lat, lon)
        distance_cible_km : distance depuis le debut

    Returns:
        tuple (lat, lon) ou None si polyline vide.
    """
    if not polyline_latlon:
        return None
    if len(polyline_latlon) == 1 or distance_cible_km <= 0:
        return polyline_latlon[0]

    distance_cumul = 0.0
    for i in range(len(polyline_latlon) - 1):
        lat_a, lon_a = polyline_latlon[i]
        lat_b, lon_b = polyline_latlon[i + 1]
        d_segment = _distance_haversine_km(lat_a, lon_a, lat_b, lon_b)

        if distance_cumul + d_segment >= distance_cible_km:
            # On est sur ce segment
            ratio = (distance_cible_km - distance_cumul) / d_segment if d_segment > 0 else 0
            lat = lat_a + ratio * (lat_b - lat_a)
            lon = lon_a + ratio * (lon_b - lon_a)
            return (lat, lon)
        distance_cumul += d_segment

    # On a depasse : on retourne le dernier point
    return polyline_latlon[-1]


def calculer_position_gps(mission, distance_parcourue_km):
    """
    Calcule la position GPS du camion a partir de la distance parcourue
    depuis le depart, en interpolant le long du trajet REEL (polylines OSRM
    si disponibles, sinon lignes droites entre villes).

    Args:
        mission                : instance Mission
        distance_parcourue_km  : float, distance depuis le depart en km

    Returns:
        tuple (latitude, longitude, troncon_actuel) ou None si pas de trajet
    """
    trajet = calculer_trajet(mission.ville_depart, mission.ville_arrivee)
    if not trajet or not trajet["troncons"]:
        return None

    troncons = trajet["troncons"]
    distance_cumul = 0.0
    distance_cible = float(distance_parcourue_km)

    for troncon in troncons:
        d_troncon = float(troncon.distance_km)

        if distance_cumul + d_troncon >= distance_cible:
            # Le camion est sur ce troncon : on interpole le long de sa polyline
            distance_dans_troncon = distance_cible - distance_cumul
            polyline = troncon.polyline_latlon  # vraie polyline si dispo, sinon ligne droite

            position = _interpoler_le_long_polyline(polyline, distance_dans_troncon)
            if position:
                return (position[0], position[1], troncon)
            return None

        distance_cumul += d_troncon

    # On a depasse : on est arrive a destination
    dernier_troncon = troncons[-1]
    polyline = dernier_troncon.polyline_latlon
    return (polyline[-1][0], polyline[-1][1], dernier_troncon)


# =============================================================================
# TIRAGE D'EVENEMENTS ALEATOIRES
# =============================================================================
def tirer_evenements(mission, minutes_simulees, troncon_actuel):
    """
    Tire aleatoirement les evenements survenant pendant cette periode de simulation.

    Pour chaque type d'evenement actif :
      - Calcule la probabilite ajustee (basee sur duree, etat route, age camion)
      - Lance un de aleatoire
      - Si succes : cree une instance EvenementMission

    Returns:
        liste des EvenementMission crees
    """
    types_actifs = TypeEvenement.objects.filter(actif=True)
    evenements_crees = []

    # Age du camion en annees
    annee_actuelle = timezone.now().year
    age_camion = annee_actuelle - mission.camion.annee_fabrication

    for type_ev in types_actifs:
        # Probabilite de base : convertit "par heure" en "par X minutes"
        proba = float(type_ev.probabilite_par_heure) * (minutes_simulees / 60.0)

        # Modificateur : etat de la route
        if type_ev.sensible_etat_route and troncon_actuel:
            etats_difficiles = ["mauvais", "tres_mauvais"]
            if troncon_actuel.etat_route in etats_difficiles:
                proba *= 2.5  # 2.5x plus de chance sur mauvaise route

        # Modificateur : age du camion
        if type_ev.sensible_age_camion:
            if age_camion > 15:
                proba *= 2.0
            elif age_camion > 10:
                proba *= 1.5

        # Tirage
        if random.random() < proba:
            # Evenement declenche !
            duree = random.randint(type_ev.duree_min_minutes, type_ev.duree_max_minutes)
            cout_min = float(type_ev.cout_min_mga)
            cout_max = float(type_ev.cout_max_mga)
            cout = round(random.uniform(cout_min, cout_max), 2) if cout_max > 0 else 0

            # Position GPS au moment de l'evenement
            position = calculer_position_gps(mission, mission.distance_parcourue_km)
            lat = Decimal(str(position[0])) if position else None
            lon = Decimal(str(position[1])) if position else None

            # Probabilite que cet evenement fasse echouer la mission
            fait_echouer = (
                type_ev.peut_faire_echouer_mission
                and random.random() < 0.25  # 25% de chance que ce soit fatal
            )

            evenement = EvenementMission.objects.create(
                mission=mission,
                type_evenement=type_ev,
                timestamp=timezone.now(),
                duree_minutes=duree,
                cout_mga=Decimal(str(cout)),
                latitude=lat,
                longitude=lon,
                troncon=troncon_actuel,
                resolu=not fait_echouer,
                fait_echouer_mission=fait_echouer,
                description=_generer_description_evenement(type_ev, troncon_actuel),
            )
            evenements_crees.append(evenement)

            # Creer la depense associee si l'evenement a un cout
            if cout > 0:
                _creer_depense_pour_evenement(evenement)

            # Si fatal, on arrete le tirage (mission echouee)
            if fait_echouer:
                break

    return evenements_crees


def _generer_description_evenement(type_ev, troncon):
    """Genere une courte description contextuelle de l'evenement."""
    contexte_route = ""
    if troncon:
        contexte_route = f" sur la {troncon.route.numero} entre {troncon.ville_depart.nom} et {troncon.ville_arrivee.nom}"
    return f"{type_ev.libelle}{contexte_route}."


def _creer_depense_pour_evenement(evenement):
    """Cree une depense automatique liee a un evenement (si applicable)."""
    from apps.finances.models import TypeDepense, Depense

    # Mapping categorie d'evenement -> code de type de depense
    mapping = {
        "mecanique": "reparation_moteur",
        "trafic": None,                    # Pas de depense
        "meteo": None,
        "controle": "frais_administratif",
        "securite": "amende",
        "humain": None,
        "infrastructure": "reparation_pneu",
        "accident": "reparation_carrosserie",
    }

    # Cas particuliers plus precis
    if evenement.type_evenement.code == "crevaison" or evenement.type_evenement.code == "nid_de_poule_majeur":
        code_depense = "reparation_pneu"
    elif evenement.type_evenement.code == "controle_gendarmerie":
        code_depense = "amende"
    elif evenement.type_evenement.code == "pesee_routiere":
        code_depense = "amende"
    elif evenement.type_evenement.code == "controle_douane":
        code_depense = "frais_douane"
    else:
        code_depense = mapping.get(evenement.type_evenement.categorie)

    if not code_depense:
        return None

    type_dep = TypeDepense.objects.filter(code=code_depense).first()
    if not type_dep:
        return None

    return Depense.objects.create(
        type_depense=type_dep,
        montant_mga=evenement.cout_mga,
        date=evenement.timestamp,
        mission=evenement.mission,
        camion=evenement.mission.camion,
        evenement=evenement,
        automatique=True,
        description=f"{evenement.type_evenement.libelle} - mission {evenement.mission.reference}",
    )


# =============================================================================
# AVANCER UNE MISSION
# =============================================================================
@transaction.atomic
def avancer_mission(mission, minutes_a_avancer):
    """
    Fait avancer une mission de N minutes simulees.
    Met a jour la distance parcourue, cree une position GPS, tire des evenements,
    et termine la mission si la distance totale est atteinte.

    Args:
        mission             : Mission en statut EN_COURS
        minutes_a_avancer   : nombre de minutes simulees a faire ecouler

    Returns:
        dict avec resume du tick : nouvelles distances, evenements crees, etc.
    """
    if mission.statut != Mission.Statut.EN_COURS:
        return {"ignored": True, "reason": "Mission pas en cours"}

    if not mission.distance_totale_km or mission.distance_totale_km == 0:
        return {"ignored": True, "reason": "Distance totale inconnue"}

    # Vitesse moyenne (km/min) basee sur la duree des troncons
    trajet = calculer_trajet(mission.ville_depart, mission.ville_arrivee)
    if not trajet or trajet["duree_minutes"] == 0:
        return {"ignored": True, "reason": "Pas de trajet calculable"}

    vitesse_km_par_min = float(trajet["distance_km"]) / trajet["duree_minutes"]

    # Calcul de la nouvelle distance
    distance_avant = float(mission.distance_parcourue_km)
    distance_max = float(mission.distance_totale_km)
    distance_apres = min(distance_avant + vitesse_km_par_min * float(minutes_a_avancer), distance_max)

    # Position GPS et troncon actuel
    position = calculer_position_gps(mission, distance_apres)
    troncon_actuel = position[2] if position else None

    # Tirer les evenements aleatoires
    evenements = tirer_evenements(mission, float(minutes_a_avancer), troncon_actuel)

    # Verifier si un evenement a fait echouer la mission
    evenement_fatal = any(e.fait_echouer_mission for e in evenements)

    # Mettre a jour la distance parcourue
    mission.distance_parcourue_km = Decimal(str(round(distance_apres, 2)))
    mission.save(update_fields=["distance_parcourue_km"])

    # Enregistrer la position GPS
    if position:
        PositionGPS.objects.create(
            mission=mission,
            timestamp=timezone.now(),
            latitude=Decimal(str(round(position[0], 6))),
            longitude=Decimal(str(round(position[1], 6))),
            vitesse_kmh=Decimal(str(round(vitesse_km_par_min * 60, 2))),
            distance_parcourue_km=mission.distance_parcourue_km,
        )

    # Verifier si la mission est terminee (arrivee atteinte ou echec fatal)
    fini = False
    if evenement_fatal:
        terminer_mission_simulee(mission, succes=False)
        fini = True
    elif distance_apres >= distance_max:
        terminer_mission_simulee(mission, succes=True)
        fini = True

    return {
        "distance_avant": distance_avant,
        "distance_apres": distance_apres,
        "evenements": len(evenements),
        "fini": fini,
        "succes": fini and not evenement_fatal,
    }


# =============================================================================
# FIN DE MISSION (avec creation de la depense carburant)
# =============================================================================
@transaction.atomic
def terminer_mission_simulee(mission, succes=True):
    """
    Termine une mission lancee par le simulateur.
    Cree automatiquement la depense de carburant pour la distance parcourue,
    puis appelle le service standard de fin de mission.
    """
    from apps.finances.models import TypeDepense, Depense
    from apps.missions.services import terminer_mission

    distance_km = float(mission.distance_parcourue_km)
    consommation = float(mission.camion.consommation_litres_100km)
    litres = (distance_km * consommation) / 100.0
    cout_carburant = round(litres * PRIX_GAZOLE_MGA_LITRE, 2)

    type_carburant = TypeDepense.objects.filter(code="carburant").first()
    if type_carburant and cout_carburant > 0:
        Depense.objects.create(
            type_depense=type_carburant,
            montant_mga=Decimal(str(cout_carburant)),
            date=timezone.now(),
            mission=mission,
            camion=mission.camion,
            automatique=True,
            description=(
                f"Carburant pour {distance_km:.0f} km a {consommation} L/100km "
                f"({litres:.1f} L a {PRIX_GAZOLE_MGA_LITRE} Ar/L)"
            ),
        )

    return terminer_mission(mission, succes=succes)
