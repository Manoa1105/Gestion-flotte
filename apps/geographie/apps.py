"""
Configuration de l'app "geographie".

Chaque app Django a un fichier apps.py qui déclare son nom complet et
quelques métadonnées. Django lit ce fichier au démarrage pour enregistrer l'app.
"""

from django.apps import AppConfig


class GeographieConfig(AppConfig):
    # Type de clé primaire par défaut pour cette app
    default_auto_field = "django.db.models.BigAutoField"

    # Chemin Python complet de l'app.
    # Comme l'app est dans le dossier apps/, le nom doit inclure "apps."
    name = "apps.geographie"

    # Nom affiché dans l'interface d'administration
    verbose_name = "Géographie de Madagascar"
