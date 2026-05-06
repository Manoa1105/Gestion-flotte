"""Vues de l'app finances : dashboard + CRUD depenses."""

import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator

from .models import Depense, TypeDepense
from .forms import DepenseForm
from . import services


# =============================================================================
# DASHBOARD FINANCES
# =============================================================================
def dashboard(request):
    """Tableau de bord financier global."""
    kpis = services.kpi_globaux()
    serie = services.serie_mensuelle(nb_mois=6)
    cats = services.depenses_par_categorie()
    rent = services.rentabilite_par_camion(top=10)

    # Preparation des donnees pour Chart.js (serialisees en JSON)
    chart_mensuel = {
        "labels": [m["label"] for m in serie],
        "revenus": [float(m["revenus"]) for m in serie],
        "depenses": [float(m["depenses"]) for m in serie],
    }
    chart_categories = {
        "labels": [c["categorie"] for c in cats],
        "data": [float(c["total"]) for c in cats],
    }

    contexte = {
        "titre_page": "Finances",
        "kpis": kpis,
        "serie": serie,
        "categories": cats,
        "rentabilite": rent,
        "chart_mensuel_json": json.dumps(chart_mensuel),
        "chart_categories_json": json.dumps(chart_categories),
    }
    return render(request, "finances/dashboard.html", contexte)


# =============================================================================
# DEPENSES : LISTE
# =============================================================================
def depense_liste(request):
    """Liste des depenses avec recherche et filtres."""
    recherche = request.GET.get("recherche", "").strip()
    categorie = request.GET.get("categorie", "").strip()

    depenses = (
        Depense.objects
        .select_related("type_depense", "mission", "camion", "chauffeur")
        .order_by("-date")
    )

    if recherche:
        depenses = depenses.filter(
            Q(type_depense__libelle__icontains=recherche)
            | Q(description__icontains=recherche)
            | Q(mission__reference__icontains=recherche)
            | Q(camion__immatriculation__icontains=recherche)
        )

    if categorie:
        depenses = depenses.filter(type_depense__categorie=categorie)

    paginator = Paginator(depenses, 30)
    page = paginator.get_page(request.GET.get("page", 1))

    contexte = {
        "titre_page": "Depenses",
        "page": page,
        "depenses": page.object_list,
        "recherche": recherche,
        "categorie_active": categorie,
        "categories": TypeDepense.Categorie.choices,
        "total_depenses": Depense.objects.count(),
    }
    return render(request, "finances/depense_liste.html", contexte)


# =============================================================================
# DEPENSES : CREATION
# =============================================================================
def depense_creer(request):
    """Saisie manuelle d'une depense."""
    if request.method == "POST":
        form = DepenseForm(request.POST)
        if form.is_valid():
            depense = form.save(commit=False)
            depense.automatique = False  # Saisie manuelle
            depense.save()
            messages.success(request, f"Depense de {depense.montant_mga} Ar enregistree.")
            return redirect("finances:depense_liste")
    else:
        form = DepenseForm()

    contexte = {"titre_page": "Nouvelle depense", "form": form, "mode": "creation"}
    return render(request, "finances/depense_form.html", contexte)


# =============================================================================
# DEPENSES : MODIFICATION
# =============================================================================
def depense_modifier(request, pk):
    """Modification d'une depense."""
    depense = get_object_or_404(Depense, pk=pk)

    if request.method == "POST":
        form = DepenseForm(request.POST, instance=depense)
        if form.is_valid():
            form.save()
            messages.success(request, "Depense modifiee.")
            return redirect("finances:depense_liste")
    else:
        form = DepenseForm(instance=depense)

    contexte = {
        "titre_page": "Modifier depense",
        "form": form,
        "depense": depense,
        "mode": "modification",
    }
    return render(request, "finances/depense_form.html", contexte)


# =============================================================================
# DEPENSES : SUPPRESSION
# =============================================================================
def depense_supprimer(request, pk):
    """Suppression d'une depense (avec confirmation)."""
    depense = get_object_or_404(Depense, pk=pk)

    if request.method == "POST":
        depense.delete()
        messages.success(request, "Depense supprimee.")
        return redirect("finances:depense_liste")

    return render(
        request,
        "finances/depense_confirmer_suppression.html",
        {"titre_page": "Supprimer depense", "depense": depense},
    )
