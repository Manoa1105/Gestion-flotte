"""
=============================================================================
Formulaires de l'app comptes
=============================================================================
Quatre formulaires :
  ConnexionForm          → formulaire de login (username + mot de passe)
  UtilisateurCreerForm   → création d'un utilisateur avec son profil
  UtilisateurModifierForm→ modification (sans toucher au mot de passe)
  ChangerMotDePasseForm  → changement de mot de passe (profil personnel)
=============================================================================
"""
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm

from .models import ProfilUtilisateur


# =============================================================================
# FORMULAIRE DE CONNEXION
# =============================================================================
class ConnexionForm(AuthenticationForm):
    """
    Hérite du formulaire Django standard AuthenticationForm.
    On réécrit juste les labels et les classes CSS pour notre design.
    La logique de vérification (hash mdp, etc.) est déjà dans AuthenticationForm.
    """
    username = forms.CharField(
        label="Nom d'utilisateur",
        widget=forms.TextInput(attrs={
            "class": "form-input",
            "placeholder": "Nom d'utilisateur",
            "autofocus": True,
        }),
    )
    password = forms.CharField(
        label="Mot de passe",
        widget=forms.PasswordInput(attrs={
            "class": "form-input",
            "placeholder": "Mot de passe",
        }),
    )


# =============================================================================
# FORMULAIRE DE CRÉATION D'UTILISATEUR
# =============================================================================
class UtilisateurCreerForm(forms.Form):
    """
    Création d'un User Django + son ProfilUtilisateur en une seule opération.
    On utilise un forms.Form (pas ModelForm) car on gère deux modèles à la fois.
    """
    username = forms.CharField(
        label="Nom d'utilisateur",
        max_length=150,
        widget=forms.TextInput(attrs={"class": "form-input"}),
    )
    prenom = forms.CharField(
        label="Prénom",
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-input"}),
    )
    nom = forms.CharField(
        label="Nom",
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-input"}),
    )
    email = forms.EmailField(
        label="Email",
        required=False,
        widget=forms.EmailInput(attrs={"class": "form-input"}),
    )
    mot_de_passe = forms.CharField(
        label="Mot de passe",
        min_length=8,
        widget=forms.PasswordInput(attrs={"class": "form-input"}),
    )
    mot_de_passe_confirmation = forms.CharField(
        label="Confirmer le mot de passe",
        widget=forms.PasswordInput(attrs={"class": "form-input"}),
    )
    role = forms.ChoiceField(
        label="Rôle",
        choices=ProfilUtilisateur.Role.choices,
        widget=forms.Select(attrs={"class": "form-input"}),
    )
    chauffeur_lie = forms.ModelChoiceField(
        label="Chauffeur associé (si rôle Chauffeur)",
        # On filtre les chauffeurs qui n'ont pas encore de compte
        queryset=None,
        required=False,
        empty_label="— Aucun —",
        widget=forms.Select(attrs={"class": "form-input"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Import ici pour éviter les imports circulaires
        from apps.flotte.models import Chauffeur
        # Seulement les chauffeurs sans compte utilisateur lié
        self.fields["chauffeur_lie"].queryset = Chauffeur.objects.filter(
            compte_utilisateur__isnull=True
        ).order_by("nom", "prenom")

    def clean(self):
        cleaned = super().clean()
        mdp1 = cleaned.get("mot_de_passe")
        mdp2 = cleaned.get("mot_de_passe_confirmation")
        if mdp1 and mdp2 and mdp1 != mdp2:
            raise forms.ValidationError("Les deux mots de passe ne correspondent pas.")
        return cleaned

    def clean_username(self):
        username = self.cleaned_data["username"]
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Ce nom d'utilisateur est déjà utilisé.")
        return username


# =============================================================================
# FORMULAIRE DE MODIFICATION D'UTILISATEUR
# =============================================================================
class UtilisateurModifierForm(forms.Form):
    """
    Modification d'un utilisateur existant (sans changer le mot de passe).
    Pour changer le mot de passe, on utilise ChangerMotDePasseForm.
    """
    prenom = forms.CharField(
        label="Prénom",
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-input"}),
    )
    nom = forms.CharField(
        label="Nom",
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-input"}),
    )
    email = forms.EmailField(
        label="Email",
        required=False,
        widget=forms.EmailInput(attrs={"class": "form-input"}),
    )
    role = forms.ChoiceField(
        label="Rôle",
        choices=ProfilUtilisateur.Role.choices,
        widget=forms.Select(attrs={"class": "form-input"}),
    )
    chauffeur_lie = forms.ModelChoiceField(
        label="Chauffeur associé (si rôle Chauffeur)",
        queryset=None,
        required=False,
        empty_label="— Aucun —",
        widget=forms.Select(attrs={"class": "form-input"}),
    )
    actif = forms.BooleanField(
        label="Compte actif",
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "h-4 w-4 text-primaire-600"}),
    )

    def __init__(self, *args, utilisateur=None, **kwargs):
        super().__init__(*args, **kwargs)
        from apps.flotte.models import Chauffeur
        # Chauffeurs disponibles = sans compte, ou celui déjà lié à cet utilisateur
        qs = Chauffeur.objects.filter(compte_utilisateur__isnull=True)
        if utilisateur:
            try:
                deja_lie = utilisateur.profil.chauffeur_lie
                if deja_lie:
                    qs = qs | Chauffeur.objects.filter(pk=deja_lie.pk)
            except AttributeError:
                pass
        self.fields["chauffeur_lie"].queryset = qs.order_by("nom", "prenom")


# =============================================================================
# FORMULAIRE DE CHANGEMENT DE MOT DE PASSE
# =============================================================================
class ChangerMotDePasseForm(PasswordChangeForm):
    """
    Hérite de PasswordChangeForm de Django (vérifie l'ancien mot de passe).
    On adapte juste les labels et les classes CSS.
    """
    old_password = forms.CharField(
        label="Mot de passe actuel",
        widget=forms.PasswordInput(attrs={"class": "form-input"}),
    )
    new_password1 = forms.CharField(
        label="Nouveau mot de passe",
        min_length=8,
        widget=forms.PasswordInput(attrs={"class": "form-input"}),
    )
    new_password2 = forms.CharField(
        label="Confirmer le nouveau mot de passe",
        widget=forms.PasswordInput(attrs={"class": "form-input"}),
    )
