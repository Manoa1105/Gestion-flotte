"""
Configuration de l'interface d'administration pour l'app geographie.

Django génère automatiquement une interface d'admin pour chaque modèle
qu'on enregistre ici. Cette interface est accessible sur /admin/.
"""

from django.contrib import admin
from .models import Region, Ville, RouteNationale, TronconRoute


# =============================================================================
# ADMIN POUR REGION
# =============================================================================
@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    """Interface admin pour les régions."""

    # Colonnes affichées dans la liste
    list_display = ("nom", "code", "chef_lieu")

    # Champs sur lesquels on peut faire une recherche textuelle
    search_fields = ("nom", "code", "chef_lieu")

    # Tri par défaut
    ordering = ("nom",)


# =============================================================================
# ADMIN POUR VILLE
# =============================================================================
@admin.register(Ville)
class VilleAdmin(admin.ModelAdmin):
    """Interface admin pour les villes."""

    list_display = (
        "nom",
        "region",
        "latitude",
        "longitude",
        "population",
        "est_chef_lieu_region",
    )

    # Filtres dans la barre latérale
    list_filter = ("region", "est_chef_lieu_region")

    search_fields = ("nom", "region__nom")

    # Affichage de la sélection région avec un menu déroulant + recherche
    autocomplete_fields = ("region",)


# =============================================================================
# ADMIN POUR ROUTE NATIONALE
# =============================================================================
@admin.register(RouteNationale)
class RouteNationaleAdmin(admin.ModelAdmin):
    """Interface admin pour les routes nationales."""

    list_display = ("numero", "nom_long", "longueur_totale_km")
    search_fields = ("numero", "nom_long")
    ordering = ("numero",)


# =============================================================================
# ADMIN POUR TRONCON
# =============================================================================
@admin.register(TronconRoute)
class TronconRouteAdmin(admin.ModelAdmin):
    """Interface admin pour les tronçons de route."""

    list_display = (
        "route",
        "ville_depart",
        "ville_arrivee",
        "distance_km",
        "duree_typique_minutes",
        "etat_route",
    )
    list_filter = ("route", "etat_route")
    search_fields = (
        "route__numero",
        "ville_depart__nom",
        "ville_arrivee__nom",
    )
    autocomplete_fields = ("route", "ville_depart", "ville_arrivee")
