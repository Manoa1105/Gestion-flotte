"""
=============================================================================
Services de l'app missions
=============================================================================
La "logique metier" qui depasse le simple CRUD est isolee ici, separee des
vues et des modeles. C'est le pattern Service Layer.

Avantages :
  - Les vues restent courtes (juste reception/redirection)
  - La logique est testable de facon isolee
  - Reutilisable depuis l'admin, des commandes management, des taches Celery, etc.

Contenu :
  - calculer_trajet(...)        : plus court chemin entre 2 villes
  - demarrer_mission(...)       : passe une mission en "en_cours"
  - terminer_mission(...)       : passe une mission en "terminee"
  - annuler_mission(...)        : passe une mission en "annulee"
=============================================================================
"""

from decimal import Decimal
from datetime import timedelta
import heapq

from django.db import transaction
from django.utils import timezone

from apps.geographie.models import TronconRoute
from apps.flotte.models import Camion, Chauffeur


# =============================================================================
# CALCUL DE TRAJET (Dijkstra sur le graphe des troncons)
# =============================================================================
def calculer_trajet(ville_depart, ville_arrivee):
    """
    Trouve le plus court chemin entre deux villes en suivant les troncons.

    Algorithme : Dijkstra (file de priorite, complexite O((V+E) log V)).
    On considere les troncons comme bidirectionnels (une route Tana-Antsirabe
    peut etre parcourue dans les deux sens).

    Args:
        ville_depart  : instance Ville (origine)
        ville_arrivee : instance Ville (destination)

    Returns:
        dict avec :
          - distance_km        : Decimal (somme des distances des troncons)
          - duree_minutes      : int (somme des durees)
          - troncons           : liste de TronconRoute traverses (dans l'ordre)
          - villes_traversees  : liste de Ville (dans l'ordre)
        Ou None si aucun chemin possible.
    """
    # Cas trivial : meme ville
    if ville_depart.pk == ville_arrivee.pk:
        return {
            "distance_km": Decimal("0"),
            "duree_minutes": 0,
            "troncons": [],
            "villes_traversees": [ville_depart],
        }

    # On charge tous les troncons en memoire (en pratique, ~25 entrees)
    # Si la base grossit, on pourrait pre-calculer un cache.
    tous_troncons = list(
        TronconRoute.objects.select_related("ville_depart", "ville_arrivee")
    )

    # Construction de la liste d'adjacence : pour chaque ville, les voisins
    # accessibles via un troncon (avec distance et duree).
    # adjacence[ville_id] = [(voisin_id, distance, duree, troncon), ...]
    adjacence = {}
    for t in tous_troncons:
        # Sens aller
        adjacence.setdefault(t.ville_depart_id, []).append(
            (t.ville_arrivee_id, float(t.distance_km), t.duree_typique_minutes, t)
        )
        # Sens retour (les routes sont bidirectionnelles)
        adjacence.setdefault(t.ville_arrivee_id, []).append(
            (t.ville_depart_id, float(t.distance_km), t.duree_typique_minutes, t)
        )

    # File de priorite (heap) : (distance_cumulee, identifiant_unique, ville_id, chemin_troncons, chemin_villes_ids)
    # L'identifiant unique evite les comparaisons quand deux entrees ont la meme distance.
    compteur = 0
    file = [(0.0, compteur, ville_depart.pk, [], [ville_depart.pk])]
    visites = set()
    duree_par_id = {ville_depart.pk: 0}

    while file:
        dist_cum, _, ville_id, chemin_troncons, chemin_villes_ids = heapq.heappop(file)

        # On a atteint la destination : on reconstruit le resultat
        if ville_id == ville_arrivee.pk:
            # Recuperer les villes traversees (instances) dans l'ordre
            from apps.geographie.models import Ville
            villes_dict = {v.pk: v for v in Ville.objects.filter(pk__in=chemin_villes_ids)}
            villes_traversees = [villes_dict[vid] for vid in chemin_villes_ids]
            return {
                "distance_km": Decimal(str(round(dist_cum, 2))),
                "duree_minutes": duree_par_id[ville_id],
                "troncons": chemin_troncons,
                "villes_traversees": villes_traversees,
            }

        if ville_id in visites:
            continue
        visites.add(ville_id)

        # Explorer les voisins
        for voisin_id, dist, duree, troncon in adjacence.get(ville_id, []):
            if voisin_id in visites:
                continue
            nouvelle_dist = dist_cum + dist
            nouvelle_duree = duree_par_id[ville_id] + duree
            duree_par_id[voisin_id] = min(
                duree_par_id.get(voisin_id, float("inf")), nouvelle_duree
            )
            compteur += 1
            heapq.heappush(file, (
                nouvelle_dist,
                compteur,
                voisin_id,
                chemin_troncons + [troncon],
                chemin_villes_ids + [voisin_id],
            ))

    # Aucun chemin trouve
    return None


# =============================================================================
# CYCLE DE VIE D'UNE MISSION
# =============================================================================
@transaction.atomic
def demarrer_mission(mission):
    """
    Demarre une mission : passe en "en_cours", met a jour les statuts
    du camion et du chauffeur, enregistre date_depart_reelle.

    Args:
        mission : instance Mission

    Returns:
        Mission mise a jour

    Raises:
        ValueError si la mission n'est pas dans un etat permettant le demarrage.
    """
    from .models import Mission

    if mission.statut != Mission.Statut.PLANIFIEE:
        raise ValueError(
            f"Impossible de demarrer une mission en statut '{mission.get_statut_display()}'. "
            f"Seules les missions planifiees peuvent etre demarrees."
        )

    if mission.camion.statut != Camion.Statut.DISPONIBLE:
        raise ValueError(
            f"Le camion {mission.camion.immatriculation} n'est pas disponible "
            f"(statut actuel : {mission.camion.get_statut_display()})."
        )

    if mission.chauffeur.statut != Chauffeur.Statut.DISPONIBLE:
        raise ValueError(
            f"Le chauffeur {mission.chauffeur.nom_complet} n'est pas disponible "
            f"(statut actuel : {mission.chauffeur.get_statut_display()})."
        )

    maintenant = timezone.now()
    mission.statut = Mission.Statut.EN_COURS
    mission.date_depart_reelle = maintenant

    # Calcul de la date d'arrivee prevue si pas deja calculee
    if not mission.date_arrivee_prevue and mission.distance_totale_km:
        # Si on a la distance mais pas la duree calculee, on refait le calcul
        trajet = calculer_trajet(mission.ville_depart, mission.ville_arrivee)
        if trajet:
            mission.date_arrivee_prevue = maintenant + timedelta(minutes=trajet["duree_minutes"])

    mission.save()

    # Mise a jour des statuts du camion et du chauffeur
    mission.camion.statut = Camion.Statut.EN_MISSION
    mission.camion.save()
    mission.chauffeur.statut = Chauffeur.Statut.EN_MISSION
    mission.chauffeur.save()

    return mission


@transaction.atomic
def terminer_mission(mission, succes=True):
    """
    Termine une mission (avec succes ou en echec).
    Libere le camion et le chauffeur.

    Args:
        mission : instance Mission
        succes  : True = "terminee", False = "echouee"
    """
    from .models import Mission

    if mission.statut != Mission.Statut.EN_COURS:
        raise ValueError(
            f"Seule une mission en cours peut etre terminee. "
            f"Statut actuel : {mission.get_statut_display()}."
        )

    mission.statut = Mission.Statut.TERMINEE if succes else Mission.Statut.ECHOUEE
    mission.date_arrivee_reelle = timezone.now()

    # Si succes, on considere la distance comme entierement parcourue
    if succes and mission.distance_totale_km:
        mission.distance_parcourue_km = mission.distance_totale_km

    mission.save()

    # Mise a jour des kilometrages et statuts
    if succes:
        mission.camion.kilometrage_total += int(mission.distance_totale_km or 0)
    mission.camion.statut = Camion.Statut.DISPONIBLE
    mission.camion.save()

    mission.chauffeur.statut = Chauffeur.Statut.DISPONIBLE
    mission.chauffeur.save()

    return mission


@transaction.atomic
def annuler_mission(mission):
    """
    Annule une mission planifiee ou en cours.
    Libere le camion et le chauffeur si necessaire.
    """
    from .models import Mission

    if mission.statut in (Mission.Statut.TERMINEE, Mission.Statut.ECHOUEE,
                          Mission.Statut.ANNULEE):
        raise ValueError(
            f"Cette mission ne peut plus etre annulee (statut : {mission.get_statut_display()})."
        )

    etait_en_cours = mission.statut == Mission.Statut.EN_COURS
    mission.statut = Mission.Statut.ANNULEE
    mission.save()

    # Si la mission etait en cours, liberer les ressources
    if etait_en_cours:
        mission.camion.statut = Camion.Statut.DISPONIBLE
        mission.camion.save()
        mission.chauffeur.statut = Chauffeur.Statut.DISPONIBLE
        mission.chauffeur.save()

    return mission
