"""
=============================================================================
asgi.py - Point d'entrée ASGI pour les fonctionnalités asynchrones
=============================================================================
ASGI = Asynchronous Server Gateway Interface : version moderne de WSGI qui
supporte les WebSockets et le code asynchrone (async/await).

Pourquoi on en aura besoin ?
Pour la simulation en temps réel : afficher la position des camions sur la
carte qui se met à jour automatiquement, sans que l'utilisateur recharge
la page. Cela passera par des WebSockets via Django Channels.

Pour l'instant ce fichier est juste prêt, on l'utilisera plus tard.

Documentation : https://docs.djangoproject.com/fr/5.0/howto/deployment/asgi/
=============================================================================
"""

import os
from django.core.asgi import get_asgi_application


# Indique à Django où trouver les paramètres
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

# Crée l'application ASGI que le serveur asynchrone va exécuter
application = get_asgi_application()
