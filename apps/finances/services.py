"""
=============================================================================
Services de l'app finances
=============================================================================
Calculs agreges pour le tableau de bord financier :
  - kpi_globaux           : CA total, depenses totales, marge nette, marge %
  - serie_mensuelle       : revenus + depenses des N derniers mois
  - depenses_par_categorie: repartition des depenses par categorie
  - rentabilite_par_camion: classement des camions par marge nette
=============================================================================
"""

from datetime import timedelta, date
from decimal import Decimal
from collections import defaultdict

from django.db.models import Sum, Count, Q, F
from django.utils import timezone

from .models import Depense, TypeDepense
from apps.missions.models import Mission
from apps.flotte.models import Camion


def _periode_par_defaut():
    """Renvoie (date_debut, date_fin) par defaut : les 6 derniers mois."""
    fin = timezone.now()
    debut = fin - timedelta(days=180)
    return debut, fin


# =============================================================================
# KPIs GLOBAUX
# =============================================================================
def kpi_globaux(date_debut=None, date_fin=None):
    """
    Calcule les indicateurs cles sur une periode.

    Returns:
        dict avec : ca_total, depenses_total, marge, marge_pourcent,
                    nb_missions, nb_missions_terminees, nb_missions_echouees
    """
    if date_debut is None or date_fin is None:
        date_debut, date_fin = _periode_par_defaut()

    # Chiffre d'affaires : somme des prix factures sur missions terminees
    ca = Mission.objects.filter(
        statut=Mission.Statut.TERMINEE,
        date_arrivee_reelle__range=(date_debut, date_fin),
    ).aggregate(total=Sum("prix_facture_mga"))["total"] or Decimal("0")

    # Depenses totales sur la periode
    depenses = Depense.objects.filter(
        date__range=(date_debut, date_fin)
    ).aggregate(total=Sum("montant_mga"))["total"] or Decimal("0")

    marge = ca - depenses
    marge_pct = float(marge / ca * 100) if ca else 0

    # Compteurs missions
    missions_periode = Mission.objects.filter(date_creation__range=(date_debut, date_fin))
    nb_total = missions_periode.count()
    nb_terminees = missions_periode.filter(statut=Mission.Statut.TERMINEE).count()
    nb_echouees = missions_periode.filter(statut=Mission.Statut.ECHOUEE).count()

    return {
        "ca_total": ca,
        "depenses_total": depenses,
        "marge": marge,
        "marge_pourcent": round(marge_pct, 1),
        "nb_missions": nb_total,
        "nb_missions_terminees": nb_terminees,
        "nb_missions_echouees": nb_echouees,
        "date_debut": date_debut,
        "date_fin": date_fin,
    }


# =============================================================================
# SERIE MENSUELLE (graphique en barres)
# =============================================================================
def serie_mensuelle(nb_mois=6):
    """
    Renvoie une liste des N derniers mois avec leurs revenus et depenses.

    Returns:
        liste de dict : [{ "label": "2026-01", "revenus": ..., "depenses": ... }, ...]
        triee chronologiquement (plus ancien en premier).
    """
    aujourd_hui = timezone.now().date().replace(day=1)
    mois_data = {}

    # Initialiser les N derniers mois a 0
    for i in range(nb_mois):
        # Calcul du premier jour du mois i mois en arriere
        annee = aujourd_hui.year
        mois = aujourd_hui.month - i
        while mois <= 0:
            mois += 12
            annee -= 1
        cle = f"{annee:04d}-{mois:02d}"
        mois_data[cle] = {"label": cle, "revenus": Decimal("0"), "depenses": Decimal("0")}

    # Date limite (debut du plus ancien mois)
    plus_ancien = sorted(mois_data.keys())[0]
    annee_a, mois_a = plus_ancien.split("-")
    date_debut = date(int(annee_a), int(mois_a), 1)

    # Revenus : missions terminees, regroupees par mois d'arrivee
    missions = Mission.objects.filter(
        statut=Mission.Statut.TERMINEE,
        date_arrivee_reelle__date__gte=date_debut,
    )
    for m in missions:
        if m.date_arrivee_reelle:
            cle = m.date_arrivee_reelle.strftime("%Y-%m")
            if cle in mois_data:
                mois_data[cle]["revenus"] += m.prix_facture_mga

    # Depenses : regroupees par mois de la depense
    depenses = Depense.objects.filter(date__date__gte=date_debut)
    for d in depenses:
        cle = d.date.strftime("%Y-%m")
        if cle in mois_data:
            mois_data[cle]["depenses"] += d.montant_mga

    # Tri chronologique
    return sorted(mois_data.values(), key=lambda x: x["label"])


# =============================================================================
# REPARTITION DES DEPENSES PAR CATEGORIE
# =============================================================================
def depenses_par_categorie(date_debut=None, date_fin=None):
    """Renvoie le total des depenses regroupees par categorie de TypeDepense."""
    if date_debut is None or date_fin is None:
        date_debut, date_fin = _periode_par_defaut()

    resultats = (
        Depense.objects.filter(date__range=(date_debut, date_fin))
        .values("type_depense__categorie")
        .annotate(total=Sum("montant_mga"), nb=Count("id"))
        .order_by("-total")
    )

    # Mapping code categorie -> libelle lisible
    libelles = dict(TypeDepense.Categorie.choices)
    return [
        {
            "categorie": libelles.get(r["type_depense__categorie"], r["type_depense__categorie"]),
            "code": r["type_depense__categorie"],
            "total": r["total"] or Decimal("0"),
            "nb": r["nb"],
        }
        for r in resultats
    ]


# =============================================================================
# RENTABILITE PAR CAMION
# =============================================================================
def rentabilite_par_camion(date_debut=None, date_fin=None, top=10):
    """
    Renvoie le top des camions tries par marge nette decroissante.

    Pour chaque camion :
      - revenus = somme(prix_facture missions terminees)
      - depenses = somme(depenses liees au camion ou a ses missions)
      - marge = revenus - depenses
    """
    if date_debut is None or date_fin is None:
        date_debut, date_fin = _periode_par_defaut()

    resultats = []
    for camion in Camion.objects.all():
        # Revenus
        revenus = Mission.objects.filter(
            camion=camion,
            statut=Mission.Statut.TERMINEE,
            date_arrivee_reelle__range=(date_debut, date_fin),
        ).aggregate(total=Sum("prix_facture_mga"))["total"] or Decimal("0")

        # Depenses : liees directement au camion OU a une mission de ce camion
        ids_missions = Mission.objects.filter(camion=camion).values_list("pk", flat=True)
        depenses = Depense.objects.filter(
            date__range=(date_debut, date_fin),
        ).filter(
            Q(camion=camion) | Q(mission_id__in=ids_missions)
        ).aggregate(total=Sum("montant_mga"))["total"] or Decimal("0")

        nb_missions = Mission.objects.filter(
            camion=camion,
            date_creation__range=(date_debut, date_fin),
        ).count()

        if revenus or depenses:  # On ignore les camions sans activite
            marge = revenus - depenses
            resultats.append({
                "camion": camion,
                "revenus": revenus,
                "depenses": depenses,
                "marge": marge,
                "marge_pourcent": float(marge / revenus * 100) if revenus else 0,
                "nb_missions": nb_missions,
            })

    # Tri par marge decroissante
    resultats.sort(key=lambda x: x["marge"], reverse=True)
    return resultats[:top]
