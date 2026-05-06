"""
=============================================================================
Vues de l'app comptes
=============================================================================
Vues d'authentification et de gestion des utilisateurs.

  connexion              → page de login (accessible sans être connecté)
  deconnexion            → logout (POST uniquement)
  profil                 → page de profil personnel + changement mot de passe
  utilisateur_liste      → liste tous les users (GESTIONNAIRE uniquement)
  utilisateur_creer      → création d'un user (GESTIONNAIRE uniquement)
  utilisateur_modifier   → modification (GESTIONNAIRE uniquement)
  utilisateur_supprimer  → suppression (GESTIONNAIRE uniquement)
=============================================================================
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.views.decorators.http import require_POST

from .models import ProfilUtilisateur
from .forms import (
    ConnexionForm,
    UtilisateurCreerForm,
    UtilisateurModifierForm,
    ChangerMotDePasseForm,
)
from .decorators import role_requis
from . import services


# =============================================================================
# CONNEXION
# =============================================================================
def connexion(request):
    """
    Page de connexion.
    GET  : affiche le formulaire.
    POST : tente l'authentification. Si OK → redirige vers la page demandée
           (paramètre ?next=) ou vers le tableau de bord.
    """
    # Si l'utilisateur est déjà connecté, on le redirige directement
    if request.user.is_authenticated:
        return redirect("core:accueil")

    if request.method == "POST":
        form = ConnexionForm(request, data=request.POST)
        if form.is_valid():
            # Django a déjà vérifié username + password dans form.is_valid()
            user = form.get_user()
            login(request, user)
            # Si Django avait sauvegardé une URL cible (?next=...), on y va
            next_url = request.GET.get("next") or "core:accueil"
            messages.success(request, f"Bienvenue, {user.username} !")
            return redirect(next_url)
    else:
        form = ConnexionForm(request)

    return render(request, "comptes/connexion.html", {
        "titre_page": "Connexion",
        "form": form,
    })


# =============================================================================
# DÉCONNEXION
# =============================================================================
@require_POST
def deconnexion(request):
    """
    Déconnecte l'utilisateur.
    DOIT être appelé en POST (sécurité : évite qu'un lien externe déconnecte).
    """
    logout(request)
    messages.info(request, "Vous avez été déconnecté.")
    return redirect("comptes:connexion")


# =============================================================================
# PROFIL PERSONNEL
# =============================================================================
@login_required
def profil(request):
    """
    Page de profil de l'utilisateur connecté.
    Affiche ses informations + un formulaire pour changer son mot de passe.
    """
    form_mdp = ChangerMotDePasseForm(user=request.user)

    if request.method == "POST":
        form_mdp = ChangerMotDePasseForm(user=request.user, data=request.POST)
        if form_mdp.is_valid():
            form_mdp.save()
            # update_session_auth_hash empêche la déconnexion après changement mdp
            update_session_auth_hash(request, form_mdp.user)
            messages.success(request, "Mot de passe modifié avec succès.")
            return redirect("comptes:profil")

    return render(request, "comptes/profil.html", {
        "titre_page": "Mon profil",
        "form_mdp": form_mdp,
    })


# =============================================================================
# LISTE DES UTILISATEURS (gestionnaire uniquement)
# =============================================================================
@role_requis("GESTIONNAIRE")
def utilisateur_liste(request):
    """Liste de tous les comptes utilisateurs."""
    utilisateurs = services.lister_utilisateurs()
    return render(request, "comptes/utilisateur_liste.html", {
        "titre_page": "Utilisateurs",
        "utilisateurs": utilisateurs,
    })


# =============================================================================
# CRÉATION D'UN UTILISATEUR (gestionnaire uniquement)
# =============================================================================
@role_requis("GESTIONNAIRE")
def utilisateur_creer(request):
    """Création d'un nouvel utilisateur avec son profil."""
    if request.method == "POST":
        form = UtilisateurCreerForm(request.POST)
        if form.is_valid():
            d = form.cleaned_data
            try:
                profil_cree = services.creer_utilisateur(
                    username=d["username"],
                    mot_de_passe=d["mot_de_passe"],
                    role=d["role"],
                    prenom=d.get("prenom", ""),
                    nom=d.get("nom", ""),
                    email=d.get("email", ""),
                    chauffeur_lie=d.get("chauffeur_lie"),
                )
                messages.success(
                    request,
                    f"Utilisateur {profil_cree.utilisateur.username} créé "
                    f"avec le rôle {profil_cree.get_role_display()}."
                )
                return redirect("comptes:utilisateur_liste")
            except ValueError as e:
                messages.error(request, str(e))
    else:
        form = UtilisateurCreerForm()

    return render(request, "comptes/utilisateur_form.html", {
        "titre_page": "Nouvel utilisateur",
        "form": form,
        "mode": "creation",
    })


# =============================================================================
# MODIFICATION D'UN UTILISATEUR (gestionnaire uniquement)
# =============================================================================
@role_requis("GESTIONNAIRE")
def utilisateur_modifier(request, pk):
    """Modification d'un utilisateur existant."""
    utilisateur = get_object_or_404(User, pk=pk)

    # Valeurs initiales du formulaire
    initial = {
        "prenom": utilisateur.first_name,
        "nom": utilisateur.last_name,
        "email": utilisateur.email,
        "actif": utilisateur.is_active,
    }
    try:
        initial["role"] = utilisateur.profil.role
        initial["chauffeur_lie"] = utilisateur.profil.chauffeur_lie
    except AttributeError:
        pass

    if request.method == "POST":
        form = UtilisateurModifierForm(
            request.POST,
            utilisateur=utilisateur,
        )
        if form.is_valid():
            d = form.cleaned_data
            services.modifier_utilisateur(
                utilisateur=utilisateur,
                prenom=d.get("prenom", ""),
                nom=d.get("nom", ""),
                email=d.get("email", ""),
                role=d["role"],
                chauffeur_lie=d.get("chauffeur_lie"),
                actif=d.get("actif", True),
            )
            messages.success(
                request,
                f"Utilisateur {utilisateur.username} modifié."
            )
            return redirect("comptes:utilisateur_liste")
    else:
        form = UtilisateurModifierForm(initial=initial, utilisateur=utilisateur)

    return render(request, "comptes/utilisateur_form.html", {
        "titre_page": f"Modifier {utilisateur.username}",
        "form": form,
        "utilisateur": utilisateur,
        "mode": "modification",
    })


# =============================================================================
# SUPPRESSION D'UN UTILISATEUR (gestionnaire uniquement)
# =============================================================================
@role_requis("GESTIONNAIRE")
def utilisateur_supprimer(request, pk):
    """Suppression d'un utilisateur (avec page de confirmation)."""
    utilisateur = get_object_or_404(User, pk=pk)

    # Un gestionnaire ne peut pas se supprimer lui-même
    if utilisateur == request.user:
        messages.error(request, "Vous ne pouvez pas supprimer votre propre compte.")
        return redirect("comptes:utilisateur_liste")

    if request.method == "POST":
        nom = utilisateur.username
        utilisateur.delete()
        messages.success(request, f"Utilisateur {nom} supprimé.")
        return redirect("comptes:utilisateur_liste")

    return render(request, "comptes/utilisateur_confirmer_suppression.html", {
        "titre_page": f"Supprimer {utilisateur.username}",
        "utilisateur": utilisateur,
    })
