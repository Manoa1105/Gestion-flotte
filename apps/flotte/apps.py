"""Configuration de l'app "flotte" : camions et chauffeurs."""

from django.apps import AppConfig


class FlotteConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.flotte"
    verbose_name = "Flotte (camions et chauffeurs)"
