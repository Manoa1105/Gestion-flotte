"""Formulaires de l'app finances."""

from django import forms
from .models import Depense


class DepenseForm(forms.ModelForm):
    """Formulaire de saisie manuelle d'une depense."""

    class Meta:
        model = Depense
        fields = [
            "type_depense",
            "montant_mga",
            "date",
            "description",
            "mission",
            "camion",
            "chauffeur",
        ]
        widgets = {
            "type_depense":  forms.Select(attrs={"class": "form-select"}),
            "montant_mga":   forms.NumberInput(attrs={"class": "form-input", "step": "0.01"}),
            "date":          forms.DateTimeInput(attrs={"class": "form-input", "type": "datetime-local"}),
            "description":   forms.Textarea(attrs={"class": "form-textarea", "rows": 2}),
            "mission":       forms.Select(attrs={"class": "form-select"}),
            "camion":        forms.Select(attrs={"class": "form-select"}),
            "chauffeur":     forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Format datetime pour HTML5
        if self.instance and self.instance.pk and self.instance.date:
            self.initial["date"] = self.instance.date.strftime("%Y-%m-%dT%H:%M")
        # Champs lies optionnels avec un choix vide explicite
        self.fields["mission"].required = False
        self.fields["camion"].required = False
        self.fields["chauffeur"].required = False
        self.fields["mission"].empty_label = "(Aucune)"
        self.fields["camion"].empty_label = "(Aucun)"
        self.fields["chauffeur"].empty_label = "(Aucun)"
