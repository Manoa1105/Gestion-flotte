"""URLs de l'app finances."""

from django.urls import path
from . import views


app_name = "finances"


urlpatterns = [
    path("",                            views.dashboard,          name="dashboard"),
    path("depenses/",                   views.depense_liste,      name="depense_liste"),
    path("depenses/nouvelle/",          views.depense_creer,      name="depense_creer"),
    path("depenses/<int:pk>/modifier/", views.depense_modifier,   name="depense_modifier"),
    path("depenses/<int:pk>/supprimer/",views.depense_supprimer,  name="depense_supprimer"),
]
