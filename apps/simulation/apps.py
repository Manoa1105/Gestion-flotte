"""Configuration de l'app "simulation"."""

from django.apps import AppConfig


class SimulationConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.simulation"
    verbose_name = "Simulation et événements"
