"""Configuration admin pour les types d'événements et événements de missions."""

from django.contrib import admin
from .models import TypeEvenement, EvenementMission


@admin.register(TypeEvenement)
class TypeEvenementAdmin(admin.ModelAdmin):
    """Interface admin pour le catalogue des types d'événements."""

    list_display = (
        "libelle",
        "categorie",
        "gravite",
        "probabilite_par_heure",
        "duree_min_minutes",
        "duree_max_minutes",
        "actif",
    )
    list_filter = ("categorie", "gravite", "actif", "peut_faire_echouer_mission")
    search_fields = ("code", "libelle", "description")
    list_editable = ("actif",)  # Bouton on/off rapide depuis la liste

    fieldsets = (
        ("Identification", {
            "fields": ("code", "libelle", "categorie", "gravite", "actif"),
        }),
        ("Probabilité et durée", {
            "fields": (
                "probabilite_par_heure",
                "duree_min_minutes",
                "duree_max_minutes",
            ),
        }),
        ("Coût", {
            "fields": ("cout_min_mga", "cout_max_mga"),
        }),
        ("Modificateurs contextuels", {
            "fields": (
                "sensible_etat_route",
                "sensible_age_camion",
                "peut_faire_echouer_mission",
            ),
        }),
        ("Description", {
            "fields": ("description",),
        }),
    )


@admin.register(EvenementMission)
class EvenementMissionAdmin(admin.ModelAdmin):
    """Interface admin pour les événements survenus pendant les missions."""

    list_display = (
        "type_evenement",
        "mission",
        "timestamp",
        "duree_minutes",
        "cout_mga",
        "resolu",
        "fait_echouer_mission",
    )
    list_filter = (
        "type_evenement__categorie",
        "type_evenement__gravite",
        "resolu",
        "fait_echouer_mission",
    )
    search_fields = (
        "mission__reference",
        "type_evenement__libelle",
        "description",
    )
    autocomplete_fields = ("mission", "type_evenement", "troncon")
    date_hierarchy = "timestamp"
    readonly_fields = ("cree_le",)
