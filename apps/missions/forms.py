"""
Formulaires de l'app missions.
"""

from datetime import timedelta
from django import forms
from django.utils import timezone

from .models import Mission
from apps.flotte.models import Camion, Chauffeur
from apps.geographie.models import Ville
from .services import calculer_trajet


class MissionForm(forms.ModelForm):
    """
    Formulaire de creation/edition d'une mission.

    Particularites :
      - Restriction des camions/chauffeurs aux disponibles (sauf en edition
        ou on garde les actuels meme si non disponibles).
      - Calcul automatique de la distance et de la date d'arrivee prevue
        a partir des troncons (dans clean()).
      - Validation : les villes depart et arrivee doivent etre differentes
        et un chemin doit exister entre elles.
    """

    class Meta:
        model = Mission
        fields = [
            "camion",
            "chauffeur",
            "ville_depart",
            "ville_arrivee",
            "categorie_cargaison",
            "description_cargaison",
            "poids_cargaison_tonnes",
            "nom_client",
            "prix_facture_mga",
            "date_depart_prevue",
            "notes",
        ]
        widgets = {
            "camion":            forms.Select(attrs={"class": "form-select"}),
            "chauffeur":         forms.Select(attrs={"class": "form-select"}),
            "ville_depart":      forms.Select(attrs={"class": "form-select"}),
            "ville_arrivee":     forms.Select(attrs={"class": "form-select"}),
            "categorie_cargaison": forms.Select(attrs={"class": "form-select"}),
            "description_cargaison": forms.Textarea(attrs={"class": "form-textarea", "rows": 2}),
            "poids_cargaison_tonnes": forms.NumberInput(attrs={"class": "form-input", "step": "0.1"}),
            "nom_client":        forms.TextInput(attrs={"class": "form-input"}),
            "prix_facture_mga":  forms.NumberInput(attrs={"class": "form-input", "step": "0.01"}),
            "date_depart_prevue": forms.DateTimeInput(attrs={
                "class": "form-input",
                "type": "datetime-local",
            }),
            "notes":             forms.Textarea(attrs={"class": "form-textarea", "rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Restreindre la liste des camions et chauffeurs.
        # En creation : uniquement les disponibles.
        # En modification : on inclut aussi le camion/chauffeur actuel meme s'il est en mission.
        camions_dispo = Camion.objects.filter(statut=Camion.Statut.DISPONIBLE)
        chauffeurs_dispo = Chauffeur.objects.filter(statut=Chauffeur.Statut.DISPONIBLE)

        if self.instance and self.instance.pk:
            # En edition : ajouter l'instance actuelle au queryset si elle n'y est pas
            if self.instance.camion_id and self.instance.camion not in camions_dispo:
                camions_dispo = Camion.objects.filter(
                    pk__in=list(camions_dispo.values_list("pk", flat=True)) + [self.instance.camion_id]
                )
            if self.instance.chauffeur_id and self.instance.chauffeur not in chauffeurs_dispo:
                chauffeurs_dispo = Chauffeur.objects.filter(
                    pk__in=list(chauffeurs_dispo.values_list("pk", flat=True)) + [self.instance.chauffeur_id]
                )

        self.fields["camion"].queryset = camions_dispo.order_by("immatriculation")
        self.fields["chauffeur"].queryset = chauffeurs_dispo.order_by("nom", "prenom")
        self.fields["ville_depart"].queryset = Ville.objects.all().order_by("nom")
        self.fields["ville_arrivee"].queryset = Ville.objects.all().order_by("nom")

        # Format datetime pour le widget HTML5
        if self.instance and self.instance.date_depart_prevue:
            self.initial["date_depart_prevue"] = self.instance.date_depart_prevue.strftime(
                "%Y-%m-%dT%H:%M"
            )

    def clean(self):
        """Validation globale + calcul automatique distance et date d'arrivee."""
        cleaned = super().clean()
        ville_depart = cleaned.get("ville_depart")
        ville_arrivee = cleaned.get("ville_arrivee")

        # Verification : depart et arrivee differents
        if ville_depart and ville_arrivee and ville_depart.pk == ville_arrivee.pk:
            raise forms.ValidationError(
                "La ville d'arrivee doit etre differente de la ville de depart."
            )

        # Calcul du trajet via les troncons
        if ville_depart and ville_arrivee:
            trajet = calculer_trajet(ville_depart, ville_arrivee)
            if not trajet:
                raise forms.ValidationError(
                    f"Aucun trajet possible entre {ville_depart} et {ville_arrivee}. "
                    f"Verifie qu'il existe une suite de troncons reliant ces villes."
                )
            # On stocke le resultat pour save()
            self._trajet_calcule = trajet

        return cleaned

    def save(self, commit=True):
        """Sauvegarde + remplit distance_totale_km et date_arrivee_prevue."""
        mission = super().save(commit=False)

        # Distance et date d'arrivee a partir du trajet calcule
        if hasattr(self, "_trajet_calcule"):
            mission.distance_totale_km = self._trajet_calcule["distance_km"]
            if mission.date_depart_prevue:
                mission.date_arrivee_prevue = mission.date_depart_prevue + timedelta(
                    minutes=self._trajet_calcule["duree_minutes"]
                )

        if commit:
            mission.save()
        return mission
