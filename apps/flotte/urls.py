"""Routage URL de l'app "flotte" : camions et chauffeurs."""

from django.urls import path
from . import views


app_name = "flotte"


urlpatterns = [
    # CAMIONS
    path("camions/",                    views.camion_liste,     name="camion_liste"),
    path("camions/nouveau/",            views.camion_creer,     name="camion_creer"),
    path("camions/<int:pk>/",           views.camion_detail,    name="camion_detail"),
    path("camions/<int:pk>/modifier/",  views.camion_modifier,  name="camion_modifier"),
    path("camions/<int:pk>/supprimer/", views.camion_supprimer, name="camion_supprimer"),

    # CHAUFFEURS
    path("chauffeurs/",                    views.chauffeur_liste,     name="chauffeur_liste"),
    path("chauffeurs/nouveau/",            views.chauffeur_creer,     name="chauffeur_creer"),
    path("chauffeurs/<int:pk>/",           views.chauffeur_detail,    name="chauffeur_detail"),
    path("chauffeurs/<int:pk>/modifier/",  views.chauffeur_modifier,  name="chauffeur_modifier"),
    path("chauffeurs/<int:pk>/supprimer/", views.chauffeur_supprimer, name="chauffeur_supprimer"),
]
