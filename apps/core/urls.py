"""
=============================================================================
Routage URL de l'app "core"
=============================================================================
Ce fichier déclare les URLs gérées par l'app core.
Il sera "inclus" dans config/urls.py via une ligne path("", include("apps.core.urls")).

Pattern usuel : chaque app a son urls.py, et le projet les agrège dans config/urls.py.
=============================================================================
"""

from django.urls import path
from . import views


# app_name est utilisé pour "namespacer" les URLs.
# On pourra référencer une URL avec {% url 'core:accueil' %} dans les templates.
app_name = "core"


urlpatterns = [
    # path(motif_url, vue_a_appeler, name=identifiant_unique)
    # Le motif "" correspond à l'URL racine de cette app.
    path("", views.accueil, name="accueil"),
]
