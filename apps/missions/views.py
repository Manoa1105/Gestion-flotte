"""
Vues de l'app missions : CRUD + actions de cycle de vie.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST
from django.http import JsonResponse

from .models import Mission
from .forms import MissionForm
from . import services


# =============================================================================
# MISSION : LISTE
# =============================================================================
def mission_liste(request):
    """Liste des missions avec recherche, filtre statut, pagination."""
    recherche = request.GET.get("recherche", "").strip()
    statut = request.GET.get("statut", "").strip()

    missions = (
        Mission.objects
        .select_related("camion", "chauffeur", "ville_depart", "ville_arrivee")
        .order_by("-date_creation")
    )

    if recherche:
        missions = missions.filter(
            Q(reference__icontains=recherche)
            | Q(ville_depart__nom__icontains=recherche)
            | Q(ville_arrivee__nom__icontains=recherche)
            | Q(camion__immatriculation__icontains=recherche)
            | Q(chauffeur__nom__icontains=recherche)
            | Q(nom_client__icontains=recherche)
        )

    if statut:
        missions = missions.filter(statut=statut)

    paginator = Paginator(missions, 20)
    page = paginator.get_page(request.GET.get("page", 1))

    contexte = {
        "titre_page": "Missions",
        "page": page,
        "missions": page.object_list,
        "recherche": recherche,
        "statut_actif": statut,
        "statuts": Mission.Statut.choices,
        "total_missions": Mission.objects.count(),
    }

    if request.headers.get("HX-Request"):
        return render(request, "missions/_mission_liste_resultats.html", contexte)

    return render(request, "missions/mission_liste.html", contexte)


# =============================================================================
# MISSION : DETAIL
# =============================================================================
def mission_detail(request, pk):
    """Page de detail d'une mission."""
    mission = get_object_or_404(
        Mission.objects.select_related(
            "camion", "chauffeur", "ville_depart", "ville_arrivee"
        ),
        pk=pk,
    )

    # Calcul du trajet pour afficher les villes traversees
    trajet = services.calculer_trajet(mission.ville_depart, mission.ville_arrivee)

    # Evenements survenus pendant la mission
    evenements = mission.evenements.select_related("type_evenement", "troncon").order_by("-timestamp")

    # Depenses generees par la mission
    depenses = mission.depenses.select_related("type_depense").order_by("-date")
    total_depenses = sum(d.montant_mga for d in depenses)
    rentabilite = mission.prix_facture_mga - total_depenses

    contexte = {
        "titre_page": mission.reference,
        "mission": mission,
        "trajet": trajet,
        "evenements": evenements,
        "depenses": depenses,
        "total_depenses": total_depenses,
        "rentabilite": rentabilite,
    }
    return render(request, "missions/mission_detail.html", contexte)


# =============================================================================
# MISSION : CREATION
# =============================================================================
def mission_creer(request):
    """Creation d'une nouvelle mission."""
    if request.method == "POST":
        form = MissionForm(request.POST)
        if form.is_valid():
            mission = form.save()
            messages.success(
                request,
                f"Mission {mission.reference} creee : "
                f"{mission.distance_totale_km} km prevus."
            )
            return redirect("missions:mission_detail", pk=mission.pk)
    else:
        form = MissionForm()

    contexte = {
        "titre_page": "Nouvelle mission",
        "form": form,
        "mode": "creation",
    }
    return render(request, "missions/mission_form.html", contexte)


# =============================================================================
# MISSION : MODIFICATION
# =============================================================================
def mission_modifier(request, pk):
    """Modification d'une mission existante."""
    mission = get_object_or_404(Mission, pk=pk)

    # On bloque la modification des missions deja en cours / terminees
    if mission.statut not in (Mission.Statut.PLANIFIEE, Mission.Statut.ANNULEE):
        messages.error(
            request,
            f"Impossible de modifier une mission en statut "
            f"'{mission.get_statut_display()}'."
        )
        return redirect("missions:mission_detail", pk=mission.pk)

    if request.method == "POST":
        form = MissionForm(request.POST, instance=mission)
        if form.is_valid():
            form.save()
            messages.success(request, f"Mission {mission.reference} modifiee.")
            return redirect("missions:mission_detail", pk=mission.pk)
    else:
        form = MissionForm(instance=mission)

    contexte = {
        "titre_page": f"Modifier {mission.reference}",
        "form": form,
        "mission": mission,
        "mode": "modification",
    }
    return render(request, "missions/mission_form.html", contexte)


# =============================================================================
# MISSION : SUPPRESSION
# =============================================================================
def mission_supprimer(request, pk):
    """Suppression d'une mission (uniquement si planifiee ou annulee)."""
    mission = get_object_or_404(Mission, pk=pk)

    if mission.statut not in (Mission.Statut.PLANIFIEE, Mission.Statut.ANNULEE):
        messages.error(
            request,
            "Seules les missions planifiees ou annulees peuvent etre supprimees. "
            "Sinon, l'historique serait perdu."
        )
        return redirect("missions:mission_detail", pk=mission.pk)

    if request.method == "POST":
        ref = mission.reference
        mission.delete()
        messages.success(request, f"Mission {ref} supprimee.")
        return redirect("missions:mission_liste")

    contexte = {
        "titre_page": f"Supprimer {mission.reference}",
        "mission": mission,
    }
    return render(request, "missions/mission_confirmer_suppression.html", contexte)


# =============================================================================
# MISSION : ACTIONS DE CYCLE DE VIE
# =============================================================================
@require_POST
def mission_demarrer(request, pk):
    """Demarre une mission planifiee."""
    mission = get_object_or_404(Mission, pk=pk)
    try:
        services.demarrer_mission(mission)
        messages.success(
            request,
            f"Mission {mission.reference} demarree. Le camion est en route."
        )
    except ValueError as e:
        messages.error(request, str(e))
    return redirect("missions:mission_detail", pk=mission.pk)


@require_POST
def mission_terminer(request, pk):
    """Termine une mission en cours (avec succes)."""
    mission = get_object_or_404(Mission, pk=pk)
    try:
        services.terminer_mission(mission, succes=True)
        messages.success(request, f"Mission {mission.reference} terminee avec succes.")
    except ValueError as e:
        messages.error(request, str(e))
    return redirect("missions:mission_detail", pk=mission.pk)


@require_POST
def mission_echouer(request, pk):
    """Marque une mission comme echouee."""
    mission = get_object_or_404(Mission, pk=pk)
    try:
        services.terminer_mission(mission, succes=False)
        messages.warning(request, f"Mission {mission.reference} marquee comme echouee.")
    except ValueError as e:
        messages.error(request, str(e))
    return redirect("missions:mission_detail", pk=mission.pk)


@require_POST
def mission_annuler(request, pk):
    """Annule une mission planifiee ou en cours."""
    mission = get_object_or_404(Mission, pk=pk)
    try:
        services.annuler_mission(mission)
        messages.success(request, f"Mission {mission.reference} annulee.")
    except ValueError as e:
        messages.error(request, str(e))
    return redirect("missions:mission_detail", pk=mission.pk)


# =============================================================================
# ENDPOINT JSON POUR LA CARTE LEAFLET
# =============================================================================
def mission_carte_data(request, pk):
    """
    Renvoie en JSON toutes les donnees necessaires a la carte Leaflet :
      - infos mission (statut, progression)
      - villes du trajet avec coordonnees
      - polyline du trajet planifie
      - position actuelle du camion
      - trace GPS reellement parcourue
      - evenements survenus avec leurs positions

    Utilise par le JavaScript de mission_detail.html pour rafraichir la carte
    sans recharger la page (polling toutes les 3 sec).
    """
    mission = get_object_or_404(Mission, pk=pk)
    trajet = services.calculer_trajet(mission.ville_depart, mission.ville_arrivee)

    # Villes du trajet avec coordonnees (pour les marqueurs)
    villes_data = []
    if trajet:
        for i, v in enumerate(trajet["villes_traversees"]):
            type_ville = "depart" if i == 0 else "arrivee" if i == len(trajet["villes_traversees"]) - 1 else "etape"
            villes_data.append({
                "nom": v.nom,
                "lat": float(v.latitude),
                "lon": float(v.longitude),
                "type": type_ville,
            })

    # Polyline du trajet planifie : on concatene les vraies polylines des
    # troncons (suit les vraies routes via OSRM). Si un troncon n'a pas de
    # polyline reelle, on retombe sur la ligne droite entre les 2 villes.
    polyline_planifiee = []
    if trajet:
        for troncon in trajet["troncons"]:
            for lat, lon in troncon.polyline_latlon:
                # Eviter les doublons aux jonctions de troncons
                if not polyline_planifiee or polyline_planifiee[-1] != [lat, lon]:
                    polyline_planifiee.append([lat, lon])
    # Si aucun troncon (cas pathologique), on tombe sur la liste des villes
    if not polyline_planifiee:
        polyline_planifiee = [[v["lat"], v["lon"]] for v in villes_data]

    # Trace GPS effectivement parcourue (positions enregistrees par le simulateur)
    positions = mission.positions.order_by("timestamp")
    trace_gps = [[float(p.latitude), float(p.longitude)] for p in positions]

    # Position actuelle du camion (derniere position enregistree)
    derniere = positions.last()
    position_camion = None
    if derniere:
        position_camion = {
            "lat": float(derniere.latitude),
            "lon": float(derniere.longitude),
            "vitesse_kmh": float(derniere.vitesse_kmh),
            "timestamp": derniere.timestamp.isoformat(),
        }

    # Evenements geolocalises
    evenements_data = []
    for ev in mission.evenements.exclude(latitude__isnull=True).select_related("type_evenement"):
        evenements_data.append({
            "libelle": ev.type_evenement.libelle,
            "categorie": ev.type_evenement.categorie,
            "gravite": ev.type_evenement.gravite,
            "lat": float(ev.latitude),
            "lon": float(ev.longitude),
            "timestamp": ev.timestamp.isoformat(),
            "duree_minutes": ev.duree_minutes,
            "fatal": ev.fait_echouer_mission,
        })

    return JsonResponse({
        "mission": {
            "reference": mission.reference,
            "statut": mission.statut,
            "progression_pourcent": mission.progression_pourcent,
            "distance_parcourue_km": float(mission.distance_parcourue_km or 0),
            "distance_totale_km": float(mission.distance_totale_km or 0),
        },
        "villes": villes_data,
        "polyline_planifiee": polyline_planifiee,
        "position_camion": position_camion,
        "trace_gps": trace_gps,
        "evenements": evenements_data,
    })
