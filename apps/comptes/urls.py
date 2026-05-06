"""URLs de l'app comptes."""
from django.urls import path
from . import views

app_name = "comptes"

urlpatterns = [
    # Authentification
    path("connexion/",    views.connexion,    name="connexion"),
    path("deconnexion/",  views.deconnexion,  name="deconnexion"),
    path("profil/",       views.profil,       name="profil"),

    # Gestion des utilisateurs (gestionnaire uniquement)
    path("utilisateurs/",                      views.utilisateur_liste,    name="utilisateur_liste"),
    path("utilisateurs/nouveau/",              views.utilisateur_creer,    name="utilisateur_creer"),
    path("utilisateurs/<int:pk>/modifier/",    views.utilisateur_modifier,  name="utilisateur_modifier"),
    path("utilisateurs/<int:pk>/supprimer/",   views.utilisateur_supprimer, name="utilisateur_supprimer"),
]
