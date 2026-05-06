"""Administration Django pour l'app comptes."""
from django.contrib import admin
from .models import ProfilUtilisateur


@admin.register(ProfilUtilisateur)
class ProfilUtilisateurAdmin(admin.ModelAdmin):
    list_display = ("utilisateur", "role", "chauffeur_lie")
    list_filter = ("role",)
    search_fields = ("utilisateur__username", "utilisateur__first_name", "utilisateur__last_name")
    raw_id_fields = ("utilisateur", "chauffeur_lie")
