"""
=============================================================================
Modèles de l'app "finances"
=============================================================================
Cette app suit l'argent qui entre et qui sort.

Trois modèles :
  - TypeDepense : catalogue des types de dépenses possibles
  - Depense     : une dépense réelle (avec montant, date, lien vers mission/camion)
  - Revenu      : un revenu lié à une mission terminée

Une dépense peut être liée :
  - à une mission (carburant consommé, péage payé pendant un trajet)
  - à un camion (réparation, vidange, assurance)
  - aux deux (réparation pendant une mission)
  - à aucun des deux (frais administratifs, salaire mensuel, etc.)

Le calcul de rentabilité d'un camion = somme(revenus de ses missions)
                                       - somme(dépenses liées à lui ou à ses missions)
=============================================================================
"""

from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal


# =============================================================================
# TYPE DE DÉPENSE (catalogue)
# =============================================================================
class TypeDepense(models.Model):
    """
    Catalogue des types de dépenses.
    On le pré-remplira avec : carburant, salaire, péage, réparation, vidange,
    assurance, amende, douane, repas chauffeur, hébergement, etc.
    """

    class Categorie(models.TextChoices):
        """Grandes familles de dépenses."""
        OPERATIONNELLE = "operationnelle", "Opérationnelle (carburant, péage)"
        RH = "rh", "Ressources humaines (salaire, prime)"
        MAINTENANCE = "maintenance", "Maintenance et réparations"
        ADMINISTRATIVE = "administrative", "Administrative (douane, amende, taxes)"
        ASSURANCE = "assurance", "Assurance"
        AUTRE = "autre", "Autre"

    code = models.SlugField(
        max_length=50,
        unique=True,
        verbose_name="Code",
        help_text="Identifiant technique (ex : carburant, peage, salaire_chauffeur)",
    )

    libelle = models.CharField(
        max_length=100,
        verbose_name="Libellé",
    )

    categorie = models.CharField(
        max_length=20,
        choices=Categorie.choices,
        default=Categorie.AUTRE,
        verbose_name="Catégorie",
    )

    description = models.TextField(
        blank=True,
        verbose_name="Description",
    )

    actif = models.BooleanField(
        default=True,
        verbose_name="Actif",
    )

    class Meta:
        verbose_name = "Type de dépense"
        verbose_name_plural = "Types de dépenses"
        ordering = ["categorie", "libelle"]

    def __str__(self):
        return self.libelle


# =============================================================================
# DÉPENSE (instance)
# =============================================================================
class Depense(models.Model):
    """
    Une dépense effectuée. Peut être :
      - automatique (générée par la simulation : carburant, événements)
      - manuelle (saisie par l'utilisateur : salaire, assurance, vidange)
    """

    type_depense = models.ForeignKey(
        TypeDepense,
        on_delete=models.PROTECT,
        related_name="depenses",
        verbose_name="Type de dépense",
    )

    montant_mga = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0"))],
        verbose_name="Montant (Ariary)",
    )

    date = models.DateTimeField(
        verbose_name="Date de la dépense",
    )

    description = models.TextField(
        blank=True,
        verbose_name="Description",
    )

    # ---- Liens optionnels ----
    # Une dépense peut être liée à une mission, à un camion, ou aux deux.
    # SET_NULL : si on supprime la mission/camion, la dépense reste en base
    # mais perd son lien.

    mission = models.ForeignKey(
        "missions.Mission",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="depenses",
        verbose_name="Mission liée",
    )

    camion = models.ForeignKey(
        "flotte.Camion",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="depenses",
        verbose_name="Camion lié",
    )

    chauffeur = models.ForeignKey(
        "flotte.Chauffeur",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="depenses",
        verbose_name="Chauffeur lié (pour salaires, primes...)",
    )

    # ---- Lien éventuel avec un événement de simulation ----
    # Une crevaison génère une dépense de type "réparation pneu".
    evenement = models.OneToOneField(
        "simulation.EvenementMission",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="depense_associee",
        verbose_name="Événement à l'origine",
    )

    # ---- Métadonnées ----
    automatique = models.BooleanField(
        default=False,
        verbose_name="Générée automatiquement",
        help_text="True si créée par la simulation, False si saisie à la main",
    )

    cree_le = models.DateTimeField(auto_now_add=True, verbose_name="Enregistrée le")

    class Meta:
        verbose_name = "Dépense"
        verbose_name_plural = "Dépenses"
        ordering = ["-date"]
        indexes = [
            models.Index(fields=["mission"]),
            models.Index(fields=["camion"]),
            models.Index(fields=["date"]),
        ]

    def __str__(self):
        return f"{self.type_depense.libelle} : {self.montant_mga} Ar le {self.date:%Y-%m-%d}"


# =============================================================================
# REVENU
# =============================================================================
class Revenu(models.Model):
    """
    Revenu généré par une mission terminée.
    Relation 1-à-1 avec Mission : une mission = au plus un revenu.
    """

    mission = models.OneToOneField(
        "missions.Mission",
        on_delete=models.CASCADE,
        related_name="revenu",
        verbose_name="Mission",
    )

    montant_mga = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0"))],
        verbose_name="Montant (Ariary)",
    )

    date_paiement = models.DateField(
        verbose_name="Date de paiement",
    )

    description = models.TextField(
        blank=True,
        verbose_name="Description",
    )

    cree_le = models.DateTimeField(auto_now_add=True, verbose_name="Enregistré le")

    class Meta:
        verbose_name = "Revenu"
        verbose_name_plural = "Revenus"
        ordering = ["-date_paiement"]

    def __str__(self):
        return f"Revenu de {self.mission.reference} : {self.montant_mga} Ar"
