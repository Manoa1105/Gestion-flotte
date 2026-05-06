"""
=============================================================================
Vues de l'app "core"
=============================================================================
Une "vue" en Django est une fonction (ou une classe) qui :
  1. Reçoit une requête HTTP entrante
  2. Effectue le travail nécessaire (souvent : aller chercher des données en BDD)
  3. Renvoie une réponse HTTP (souvent : une page HTML générée à partir d'un template)

On utilise ici des Function-Based Views (FBV) : chaque vue est une fonction.
=============================================================================
"""

from django.shortcuts import render

# On importe les modèles des autres apps pour calculer les stats du dashboard
from apps.flotte.models import Camion, Chauffeur
from apps.missions.models import Mission
from apps.geographie.models import Ville


# =============================================================================
# VUE : ACCUEIL / TABLEAU DE BORD
# =============================================================================
def accueil(request):
    """
    Page d'accueil : tableau de bord avec les statistiques principales.

    Args:
        request: l'objet HttpRequest envoyé par Django (contient infos
                 sur la requête HTTP : utilisateur, GET/POST, headers, etc.)

    Returns:
        HttpResponse contenant le HTML rendu
    """

    # ---- Statistiques sur les camions ----
    # .count() compte le nombre d'objets en base.
    # .filter(statut=...) restreint aux objets dont le statut correspond.
    # Chaque appel = 1 requête SQL ; pour 4 lignes ici c'est OK.
    nb_camions_total = Camion.objects.count()
    nb_camions_dispo = Camion.objects.filter(statut=Camion.Statut.DISPONIBLE).count()
    nb_camions_mission = Camion.objects.filter(statut=Camion.Statut.EN_MISSION).count()
    nb_camions_panne = Camion.objects.filter(statut=Camion.Statut.EN_PANNE).count()

    # ---- Statistiques sur les chauffeurs ----
    nb_chauffeurs_total = Chauffeur.objects.count()
    nb_chauffeurs_dispo = Chauffeur.objects.filter(
        statut=Chauffeur.Statut.DISPONIBLE
    ).count()

    # ---- Statistiques sur les missions ----
    nb_missions_total = Mission.objects.count()
    nb_missions_en_cours = Mission.objects.filter(
        statut=Mission.Statut.EN_COURS
    ).count()
    nb_missions_planifiees = Mission.objects.filter(
        statut=Mission.Statut.PLANIFIEE
    ).count()
    nb_missions_terminees = Mission.objects.filter(
        statut=Mission.Statut.TERMINEE
    ).count()

    # ---- Statistique géographie ----
    nb_villes = Ville.objects.count()

    # ---- 5 dernières missions créées (pour l'affichage) ----
    # On limite avec [:5] pour récupérer seulement 5 enregistrements.
    # select_related() = jointure SQL pour tirer en une requête les FK liées,
    # évite le problème "N+1 requêtes" si on accède aux objets liés dans le template.
    dernieres_missions = (
        Mission.objects
        .select_related("camion", "chauffeur", "ville_depart", "ville_arrivee")
        .order_by("-date_creation")[:5]
    )

    # ---- On regroupe tout dans un dictionnaire de "contexte" ----
    # Le contexte est ce qu'on passe au template ; chaque clé devient une variable
    # accessible dans le HTML via {{ nom_de_la_cle }}.
    contexte = {
        "titre_page": "Tableau de bord",
        # Camions
        "nb_camions_total": nb_camions_total,
        "nb_camions_dispo": nb_camions_dispo,
        "nb_camions_mission": nb_camions_mission,
        "nb_camions_panne": nb_camions_panne,
        # Chauffeurs
        "nb_chauffeurs_total": nb_chauffeurs_total,
        "nb_chauffeurs_dispo": nb_chauffeurs_dispo,
        # Missions
        "nb_missions_total": nb_missions_total,
        "nb_missions_en_cours": nb_missions_en_cours,
        "nb_missions_planifiees": nb_missions_planifiees,
        "nb_missions_terminees": nb_missions_terminees,
        # Géographie
        "nb_villes": nb_villes,
        # Liste
        "dernieres_missions": dernieres_missions,
    }

    # render() prend la requête, le chemin du template et le contexte,
    # et renvoie une réponse HTML prête à l'emploi.
    return render(request, "core/accueil.html", contexte)
