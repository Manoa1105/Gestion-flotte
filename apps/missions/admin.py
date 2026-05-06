"""Configuration admin pour les missions et positions GPS."""

from django.contrib import admin
from .models import Mission, PositionGPS


# =============================================================================
# INLINE : afficher les positions GPS directement sous une mission
# =============================================================================
class PositionGPSInline(admin.TabularInline):
    """
    Permet d'afficher les positions GPS d'une mission directement
    dans la page d'édition de la mission. Lecture seule pour ne pas
    polluer manuellement les données simulées.
    """
    model = PositionGPS
    extra = 0  # Pas de lignes vides à pré-créer
    can_delete = False
    readonly_fields = (
        "timestamp",
        "latitude",
        "longitude",
        "vitesse_kmh",
        "distance_parcourue_km",
    )
    # On limite à 20 dernières positions pour ne pas faire planter l'admin
    # quand il y aura des milliers de points GPS
    max_num = 20

    def has_add_permission(self, request, obj=None):
        # On n'ajoute pas de positions GPS à la main : c'est la simulation qui le fait
        return False


@admin.register(Mission)
class MissionAdmin(admin.ModelAdmin):
    """Interface admin pour les missions."""

    list_display = (
        "reference",
        "ville_depart",
        "ville_arrivee",
        "camion",
        "chauffeur",
        "categorie_cargaison",
        "statut",
        "date_depart_prevue",
        "prix_facture_mga",
    )
    list_filter = (
        "statut",
        "categorie_cargaison",
        "date_depart_prevue",
    )
    search_fields = (
        "reference",
        "ville_depart__nom",
        "ville_arrivee__nom",
        "camion__immatriculation",
        "chauffeur__nom",
        "chauffeur__prenom",
        "nom_client",
    )
    autocomplete_fields = (
        "camion",
        "chauffeur",
        "ville_depart",
        "ville_arrivee",
    )
    readonly_fields = (
        "reference",
        "date_creation",
        "distance_parcourue_km",
        "progression_pourcent",
    )
    date_hierarchy = "date_depart_prevue"

    fieldsets = (
        ("Référence et statut", {
            "fields": ("reference", "statut", "progression_pourcent"),
        }),
        ("Ressources assignées", {
            "fields": ("camion", "chauffeur"),
        }),
        ("Trajet", {
            "fields": (
                "ville_depart",
                "ville_arrivee",
                "distance_totale_km",
                "distance_parcourue_km",
            ),
        }),
        ("Cargaison", {
            "fields": (
                "categorie_cargaison",
                "description_cargaison",
                "poids_cargaison_tonnes",
            ),
        }),
        ("Aspect financier et client", {
            "fields": ("nom_client", "prix_facture_mga"),
        }),
        ("Dates", {
            "fields": (
                "date_creation",
                "date_depart_prevue",
                "date_depart_reelle",
                "date_arrivee_prevue",
                "date_arrivee_reelle",
            ),
        }),
        ("Notes", {
            "fields": ("notes",),
        }),
    )

    inlines = [PositionGPSInline]


@admin.register(PositionGPS)
class PositionGPSAdmin(admin.ModelAdmin):
    """
    Interface admin pour les positions GPS.
    Surtout utile pour le debug - en pratique, la simulation génère
    ces données automatiquement.
    """
    list_display = (
        "mission",
        "timestamp",
        "latitude",
        "longitude",
        "vitesse_kmh",
        "distance_parcourue_km",
    )
    list_filter = ("mission",)
    search_fields = ("mission__reference",)
    date_hierarchy = "timestamp"
    readonly_fields = (
        "mission",
        "timestamp",
        "latitude",
        "longitude",
        "vitesse_kmh",
        "distance_parcourue_km",
    )
