"""
=============================================================================
wsgi.py - Point d'entrée WSGI pour les serveurs web classiques
=============================================================================
WSGI = Web Server Gateway Interface : standard Python pour qu'un serveur web
(Gunicorn, uWSGI, Apache mod_wsgi...) puisse exécuter une application Python.

Tu n'utiliseras pas ce fichier directement en développement
(Django a son propre serveur intégré : python manage.py runserver).
Il sera utilisé en production pour servir l'app aux utilisateurs.

Documentation : https://docs.djangoproject.com/fr/5.0/howto/deployment/wsgi/
=============================================================================
"""

import os
from django.core.wsgi import get_wsgi_application


# Indique à Django où trouver les paramètres
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

# Crée l'application WSGI que le serveur web va exécuter
application = get_wsgi_application()
