#!/usr/bin/env python
"""
=============================================================================
manage.py - Script de gestion principal du projet Django
=============================================================================
À quoi ça sert ?
C'est LE fichier que tu utilises tout le temps en développement Django.
Il permet de lancer toutes les commandes de gestion :

    python manage.py runserver          # Démarre le serveur de développement
    python manage.py makemigrations     # Crée les migrations de base de données
    python manage.py migrate            # Applique les migrations
    python manage.py createsuperuser    # Crée un compte admin
    python manage.py shell              # Ouvre un shell Python avec Django chargé
    python manage.py startapp NOM       # Crée une nouvelle app Django

Tu n'as normalement PAS à modifier ce fichier.
=============================================================================
"""
import os
import sys


def main():
    """Point d'entrée du script : exécute la commande Django demandée."""

    # On indique à Django où trouver les paramètres du projet.
    # "config.settings" signifie : fichier "settings.py" dans le dossier "config".
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        # Erreur typique : Django n'est pas installé ou le venv n'est pas activé.
        raise ImportError(
            "Impossible d'importer Django. Vérifie qu'il est bien installé et "
            "que ton environnement virtuel est activé. "
            "Pour installer : pip install -r requirements.txt"
        ) from exc

    # On passe les arguments de la ligne de commande à Django.
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
