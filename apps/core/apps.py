"""
Configuration de l'app "core".

L'app core héberge ce qui est commun à tout le projet :
  - La page d'accueil / tableau de bord
  - Les vues d'erreur personnalisées (404, 500)
  - Les filtres de templates ou utilitaires partagés
"""

from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.core"
    verbose_name = "Cœur de l'application"
