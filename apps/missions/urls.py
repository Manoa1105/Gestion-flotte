"""URLs de l'app missions."""

from django.urls import path
from . import views


app_name = "missions"


urlpatterns = [
    path("",                          views.mission_liste,     name="mission_liste"),
    path("nouvelle/",                 views.mission_creer,     name="mission_creer"),
    path("<int:pk>/",                 views.mission_detail,    name="mission_detail"),
    path("<int:pk>/modifier/",        views.mission_modifier,  name="mission_modifier"),
    path("<int:pk>/supprimer/",       views.mission_supprimer, name="mission_supprimer"),
    path("<int:pk>/demarrer/",        views.mission_demarrer,  name="mission_demarrer"),
    path("<int:pk>/terminer/",        views.mission_terminer,  name="mission_terminer"),
    path("<int:pk>/echouer/",         views.mission_echouer,   name="mission_echouer"),
    path("<int:pk>/annuler/",         views.mission_annuler,   name="mission_annuler"),
    path("<int:pk>/carte-data/",      views.mission_carte_data,name="mission_carte_data"),
]
