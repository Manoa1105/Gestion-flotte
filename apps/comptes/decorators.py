"""
=============================================================================
Décorateurs d'autorisation — app comptes
=============================================================================
Ces décorateurs s'ajoutent au-dessus des vues pour en contrôler l'accès.

Usage dans une vue :
    @role_requis("GESTIONNAIRE")
    def ma_vue_admin(request): ...

    @role_requis("GESTIONNAIRE", "COMPTABLE")
    def ma_vue_finances(request): ...

Si l'utilisateur n'est pas connecté → redirigé vers la page de connexion.
Si l'utilisateur est connecté mais n'a pas le bon rôle → page 403 (Interdit).
Les superusers Django (createsuperuser) contournent tous les contrôles.
=============================================================================
"""
from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def role_requis(*roles):
    """
    Vérifie que l'utilisateur connecté possède l'un des rôles listés.

    Enchaîne automatiquement @login_required : inutile de le mettre en plus.

    Paramètres :
        *roles : une ou plusieurs chaînes parmi "GESTIONNAIRE", "COMPTABLE",
                 "CHAUFFEUR"

    Exemple :
        @role_requis("GESTIONNAIRE")            # un seul rôle autorisé
        @role_requis("GESTIONNAIRE", "COMPTABLE")  # plusieurs rôles autorisés
    """
    def decorateur(vue):
        @login_required          # redirige vers LOGIN_URL si non connecté
        @wraps(vue)              # conserve le nom/docstring de la vue originale
        def vue_protegee(request, *args, **kwargs):
            # Les superusers Django ont toujours accès (compte admin technique)
            if request.user.is_superuser:
                return vue(request, *args, **kwargs)
            # Récupération du rôle via le profil lié au User
            try:
                role_actuel = request.user.profil.role
            except AttributeError:
                # L'utilisateur n'a pas de ProfilUtilisateur : accès refusé
                raise PermissionDenied
            if role_actuel not in roles:
                raise PermissionDenied
            return vue(request, *args, **kwargs)
        return vue_protegee
    return decorateur
