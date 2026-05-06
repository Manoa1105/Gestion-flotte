"""
=============================================================================
Formulaires de l'app "flotte"
=============================================================================
Un formulaire Django :
  - convertit les données POST en objets Python
  - valide ces données (champs requis, formats, contraintes)
  - génère le HTML des champs si on le souhaite
  - sauvegarde en base si tout est valide

ModelForm = formulaire automatiquement construit à partir d'un modèle.
On indique juste quels champs afficher, et Django fait le reste.
=============================================================================
"""

from django import forms
from .models import Camion, Chauffeur


# =============================================================================
# FORMULAIRE : CAMION
# =============================================================================
class CamionForm(forms.ModelForm):
    """
    Formulaire de création/édition d'un camion.
    Le HTML est généré automatiquement à partir des champs du modèle.
    """

    class Meta:
        # Modèle source pour générer les champs
        model = Camion

        # Liste explicite des champs à afficher dans le formulaire.
        # On exclut volontairement : kilometrage_total (mis à jour automatiquement
        # par les missions), cree_le et modifie_le (gérés par Django).
        fields = [
            "immatriculation",
            "marque",
            "modele",
            "annee_fabrication",
            "capacite_charge_tonnes",
            "consommation_litres_100km",
            "date_acquisition",
            "prix_acquisition_mga",
            "statut",
            "photo",
            "notes",
        ]

        # Personnalisation des widgets HTML générés.
        # Permet d'ajouter des classes CSS Tailwind pour le style.
        widgets = {
            "immatriculation": forms.TextInput(attrs={
                "class": "form-input",
                "placeholder": "Ex : 1234 TBC",
            }),
            "marque": forms.TextInput(attrs={
                "class": "form-input",
                "placeholder": "Mercedes, Volvo, Scania...",
            }),
            "modele": forms.TextInput(attrs={
                "class": "form-input",
                "placeholder": "Actros, FH16, R450...",
            }),
            "annee_fabrication": forms.NumberInput(attrs={
                "class": "form-input",
                "min": 1980,
                "max": 2030,
            }),
            "capacite_charge_tonnes": forms.NumberInput(attrs={
                "class": "form-input",
                "step": "0.1",
            }),
            "consommation_litres_100km": forms.NumberInput(attrs={
                "class": "form-input",
                "step": "0.1",
            }),
            "date_acquisition": forms.DateInput(attrs={
                "class": "form-input",
                "type": "date",  # Active le date picker natif du navigateur
            }),
            "prix_acquisition_mga": forms.NumberInput(attrs={
                "class": "form-input",
                "step": "0.01",
            }),
            "statut": forms.Select(attrs={
                "class": "form-select",
            }),
            "notes": forms.Textarea(attrs={
                "class": "form-textarea",
                "rows": 3,
            }),
        }

    def clean_immatriculation(self):
        """
        Validation personnalisée du champ immatriculation.
        Méthode magique : Django appelle automatiquement clean_<nom_du_champ>.
        On normalise en majuscules et on retire les espaces parasites.
        """
        immat = self.cleaned_data.get("immatriculation", "")
        # Normalisation : majuscules, espaces simples
        return " ".join(immat.upper().split())


# =============================================================================
# FORMULAIRE : CHAUFFEUR (préparé pour l'étape 6)
# =============================================================================
class ChauffeurForm(forms.ModelForm):
    """Formulaire de création/édition d'un chauffeur."""

    class Meta:
        model = Chauffeur
        fields = [
            "nom",
            "prenom",
            "date_naissance",
            "telephone",
            "email",
            "numero_permis",
            "type_permis",
            "annees_experience",
            "date_embauche",
            "salaire_mensuel_mga",
            "statut",
            "notes",
        ]
        widgets = {
            "nom": forms.TextInput(attrs={"class": "form-input"}),
            "prenom": forms.TextInput(attrs={"class": "form-input"}),
            "date_naissance": forms.DateInput(attrs={"class": "form-input", "type": "date"}),
            "telephone": forms.TextInput(attrs={"class": "form-input"}),
            "email": forms.EmailInput(attrs={"class": "form-input"}),
            "numero_permis": forms.TextInput(attrs={"class": "form-input"}),
            "type_permis": forms.Select(attrs={"class": "form-select"}),
            "annees_experience": forms.NumberInput(attrs={"class": "form-input", "min": 0}),
            "date_embauche": forms.DateInput(attrs={"class": "form-input", "type": "date"}),
            "salaire_mensuel_mga": forms.NumberInput(attrs={"class": "form-input", "step": "0.01"}),
            "statut": forms.Select(attrs={"class": "form-select"}),
            "notes": forms.Textarea(attrs={"class": "form-textarea", "rows": 3}),
        }
