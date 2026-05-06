"""Configuration admin pour les camions et chauffeurs."""

from django.contrib import admin
from .models import Camion, Chauffeur


@admin.register(Camion)
class CamionAdmin(admin.ModelAdmin):
    """Interface admin pour les camions."""

    list_display = (
        "immatriculation",
        "marque",
        "modele",
        "annee_fabrication",
        "capacite_charge_tonnes",
        "kilometrage_total",
        "statut",
    )
    list_filter = ("statut", "marque", "annee_fabrication")
    search_fields = ("immatriculation", "marque", "modele")
    ordering = ("immatriculation",)

    # Regroupement des champs en sections dans le formulaire d'édition
    fieldsets = (
        ("Identification", {
            "fields": ("immatriculation", "marque", "modele", "annee_fabrication", "photo"),
        }),
        ("Caractéristiques techniques", {
            "fields": (
                "capacite_charge_tonnes",
                "consommation_litres_100km",
                "kilometrage_total",
            ),
        }),
        ("Acquisition", {
            "fields": ("date_acquisition", "prix_acquisition_mga"),
        }),
        ("État", {
            "fields": ("statut", "notes"),
        }),
        ("Traçabilité", {
            "fields": ("cree_le", "modifie_le"),
            "classes": ("collapse",),  # Section repliable par défaut
        }),
    )

    readonly_fields = ("cree_le", "modifie_le")


@admin.register(Chauffeur)
class ChauffeurAdmin(admin.ModelAdmin):
    """Interface admin pour les chauffeurs."""

    list_display = (
        "nom",
        "prenom",
        "type_permis",
        "annees_experience",
        "statut",
        "telephone",
    )
    list_filter = ("statut", "type_permis")
    search_fields = ("nom", "prenom", "numero_permis", "telephone")
    ordering = ("nom", "prenom")

    fieldsets = (
        ("Identité", {
            "fields": ("nom", "prenom", "date_naissance", "telephone", "email"),
        }),
        ("Permis et expérience", {
            "fields": ("numero_permis", "type_permis", "annees_experience"),
        }),
        ("Contrat", {
            "fields": ("date_embauche", "salaire_mensuel_mga"),
        }),
        ("État", {
            "fields": ("statut", "notes"),
        }),
        ("Traçabilité", {
            "fields": ("cree_le", "modifie_le"),
            "classes": ("collapse",),
        }),
    )

    readonly_fields = ("cree_le", "modifie_le")
