"""
=============================================================================
Services de l'app comptes
=============================================================================
Fonctions métier liées à la gestion des utilisateurs.
Séparation vues / logique métier : les vues appellent ces fonctions.
=============================================================================
"""
from django.contrib.auth.models import User
from .models import ProfilUtilisateur


def creer_utilisateur(username, mot_de_passe, role, prenom="", nom="",
                      email="", chauffeur_lie=None):
    """
    Crée un User Django et son ProfilUtilisateur associé.

    Retourne le ProfilUtilisateur créé.
    Lève ValueError si le username est déjà pris.
    """
    if User.objects.filter(username=username).exists():
        raise ValueError(f"Le nom d'utilisateur '{username}' est déjà utilisé.")

    user = User.objects.create_user(
        username=username,
        password=mot_de_passe,
        first_name=prenom,
        last_name=nom,
        email=email,
    )
    profil = ProfilUtilisateur.objects.create(
        utilisateur=user,
        role=role,
        chauffeur_lie=chauffeur_lie,
    )
    return profil


def modifier_utilisateur(utilisateur, prenom="", nom="", email="",
                         role=None, chauffeur_lie=None, actif=True):
    """
    Met à jour un User Django et son ProfilUtilisateur.

    Paramètres :
        utilisateur : instance User Django
        chauffeur_lie : instance Chauffeur ou None
    """
    utilisateur.first_name = prenom
    utilisateur.last_name = nom
    utilisateur.email = email
    utilisateur.is_active = actif
    utilisateur.save()

    profil = utilisateur.profil
    if role:
        profil.role = role
    profil.chauffeur_lie = chauffeur_lie
    profil.save()


def lister_utilisateurs():
    """Retourne tous les utilisateurs avec leur profil, ordonnés par username."""
    return (
        User.objects
        .select_related("profil", "profil__chauffeur_lie")
        .order_by("username")
    )
