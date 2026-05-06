"""Configuration admin pour les types de dépenses, dépenses et revenus."""

from django.contrib import admin
from .models import TypeDepense, Depense, Revenu


@admin.register(TypeDepense)
class TypeDepenseAdmin(admin.ModelAdmin):
    """Interface admin pour le catalogue des types de dépenses."""

    list_display = ("libelle", "code", "categorie", "actif")
    list_filter = ("categorie", "actif")
    search_fields = ("code", "libelle", "description")
    list_editable = ("actif",)
    ordering = ("categorie", "libelle")


@admin.register(Depense)
class DepenseAdmin(admin.ModelAdmin):
    """Interface admin pour les dépenses."""

    list_display = (
        "date",
        "type_depense",
        "montant_mga",
        "mission",
        "camion",
        "chauffeur",
        "automatique",
    )
    list_filter = (
        "type_depense__categorie",
        "type_depense",
        "automatique",
        "date",
    )
    search_fields = (
        "type_depense__libelle",
        "description",
        "mission__reference",
        "camion__immatriculation",
    )
    autocomplete_fields = (
        "type_depense",
        "mission",
        "camion",
        "chauffeur",
        "evenement",
    )
    date_hierarchy = "date"
    readonly_fields = ("cree_le",)

    fieldsets = (
        ("Dépense", {
            "fields": ("type_depense", "montant_mga", "date", "description"),
        }),
        ("Liens (optionnels)", {
            "fields": ("mission", "camion", "chauffeur", "evenement"),
        }),
        ("Métadonnées", {
            "fields": ("automatique", "cree_le"),
            "classes": ("collapse",),
        }),
    )


@admin.register(Revenu)
class RevenuAdmin(admin.ModelAdmin):
    """Interface admin pour les revenus."""

    list_display = ("mission", "montant_mga", "date_paiement")
    list_filter = ("date_paiement",)
    search_fields = ("mission__reference", "description")
    autocomplete_fields = ("mission",)
    date_hierarchy = "date_paiement"
    readonly_fields = ("cree_le",)
