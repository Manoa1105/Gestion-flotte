"""
=============================================================================
Modèles de l'app "simulation"
=============================================================================
Cette app gère le moteur d'événements aléatoires durant les missions.

Deux modèles complémentaires :
  - TypeEvenement     : CATALOGUE des événements possibles avec leurs
                        probabilités et impacts (créé une fois pour toutes)
  - EvenementMission  : INSTANCE d'un événement qui s'est réellement produit
                        durant une mission précise

Exemple :
  TypeEvenement "Crevaison"   : probabilité 2 %/heure, durée 30-90 min, coût 50k-200k Ar
  EvenementMission #42        : type=Crevaison, mission=MIS-2026-0001,
                                heure=14h32, durée=47 min, coût=120k Ar
=============================================================================
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal


# =============================================================================
# TYPE D'ÉVÉNEMENT (catalogue)
# =============================================================================
class TypeEvenement(models.Model):
    """
    Catalogue des types d'événements possibles durant une mission.
    On le pré-remplira avec une trentaine d'événements réalistes
    (panne moteur, crevaison, embouteillage, contrôle police, pluie, etc.).
    """

    # ---- Énumérations ----
    class Categorie(models.TextChoices):
        """Grandes familles d'événements."""
        MECANIQUE = "mecanique", "Problème mécanique"
        TRAFIC = "trafic", "Trafic routier"
        METEO = "meteo", "Conditions météorologiques"
        CONTROLE = "controle", "Contrôle administratif"
        SECURITE = "securite", "Sécurité (vol, agression)"
        HUMAIN = "humain", "Facteur humain (chauffeur)"
        INFRASTRUCTURE = "infrastructure", "Infrastructure routière"
        ACCIDENT = "accident", "Accident"
        AUTRE = "autre", "Autre"

    class Gravite(models.TextChoices):
        """Niveau de gravité d'un événement."""
        MINEURE = "mineure", "Mineure (< 30 min)"
        MODEREE = "moderee", "Modérée (30 min - 2h)"
        GRAVE = "grave", "Grave (2h - 6h)"
        CRITIQUE = "critique", "Critique (> 6h, peut faire échouer la mission)"

    # ---- Identification ----
    code = models.SlugField(
        max_length=50,
        unique=True,
        verbose_name="Code",
        help_text="Identifiant technique (ex: panne_moteur, crevaison, controle_gendarmerie)",
    )

    libelle = models.CharField(
        max_length=100,
        verbose_name="Libellé",
        help_text="Nom affiché à l'utilisateur",
    )

    categorie = models.CharField(
        max_length=20,
        choices=Categorie.choices,
        verbose_name="Catégorie",
    )

    gravite = models.CharField(
        max_length=20,
        choices=Gravite.choices,
        default=Gravite.MINEURE,
        verbose_name="Gravité",
    )

    # ---- Paramètres de simulation ----
    probabilite_par_heure = models.DecimalField(
        max_digits=6,
        decimal_places=4,
        validators=[MinValueValidator(Decimal("0")), MaxValueValidator(Decimal("1"))],
        verbose_name="Probabilité par heure de trajet (0-1)",
        help_text="Ex : 0.0200 = 2 % de chance par heure de trajet",
    )

    duree_min_minutes = models.PositiveIntegerField(
        verbose_name="Durée minimum (minutes)",
        help_text="Durée minimum de l'événement (immobilisation)",
    )

    duree_max_minutes = models.PositiveIntegerField(
        verbose_name="Durée maximum (minutes)",
    )

    cout_min_mga = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0"),
        verbose_name="Coût minimum (Ariary)",
        help_text="Coût minimum généré par cet événement (réparation, amende, perte)",
    )

    cout_max_mga = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0"),
        verbose_name="Coût maximum (Ariary)",
    )

    # ---- Modificateurs contextuels (pour plus tard) ----
    sensible_etat_route = models.BooleanField(
        default=False,
        verbose_name="Probabilité dépend de l'état de la route",
        help_text="Si coché, la probabilité augmente sur les mauvaises routes",
    )

    sensible_age_camion = models.BooleanField(
        default=False,
        verbose_name="Probabilité dépend de l'âge du camion",
        help_text="Si coché, la probabilité augmente avec l'âge du camion",
    )

    peut_faire_echouer_mission = models.BooleanField(
        default=False,
        verbose_name="Peut faire échouer la mission",
        help_text="Si coché, cet événement peut entraîner l'échec total de la mission",
    )

    # ---- Description ----
    description = models.TextField(
        blank=True,
        verbose_name="Description",
        help_text="Description longue, contexte, exemples concrets",
    )

    actif = models.BooleanField(
        default=True,
        verbose_name="Actif",
        help_text="Si décoché, cet événement ne sera plus tiré par la simulation",
    )

    class Meta:
        verbose_name = "Type d'événement"
        verbose_name_plural = "Types d'événements"
        ordering = ["categorie", "libelle"]

    def __str__(self):
        return f"{self.libelle} ({self.get_gravite_display()})"


# =============================================================================
# ÉVÉNEMENT DE MISSION (instance)
# =============================================================================
class EvenementMission(models.Model):
    """
    Instance d'un événement qui s'est réellement produit pendant une mission.
    Créé par le moteur de simulation avec les valeurs concrètes (durée tirée
    aléatoirement entre min et max, coût calculé, position GPS, etc.).
    """

    mission = models.ForeignKey(
        "missions.Mission",
        on_delete=models.CASCADE,
        related_name="evenements",
        verbose_name="Mission",
    )

    type_evenement = models.ForeignKey(
        TypeEvenement,
        on_delete=models.PROTECT,
        related_name="instances",
        verbose_name="Type d'événement",
    )

    # ---- Quand ----
    timestamp = models.DateTimeField(
        verbose_name="Survenu le",
        help_text="Date et heure de début de l'événement",
    )

    duree_minutes = models.PositiveIntegerField(
        verbose_name="Durée effective (minutes)",
    )

    # ---- Où ----
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        verbose_name="Latitude",
    )

    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        verbose_name="Longitude",
    )

    troncon = models.ForeignKey(
        "geographie.TronconRoute",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Tronçon où l'événement est survenu",
    )

    # ---- Combien ----
    cout_mga = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0"),
        verbose_name="Coût engendré (Ariary)",
    )

    # ---- Détails ----
    description = models.TextField(
        blank=True,
        verbose_name="Description détaillée",
        help_text="Récit de ce qui s'est passé, généré automatiquement ou édité",
    )

    resolu = models.BooleanField(
        default=True,
        verbose_name="Résolu",
        help_text="L'événement a-t-il été résolu et le camion a-t-il pu repartir ?",
    )

    fait_echouer_mission = models.BooleanField(
        default=False,
        verbose_name="A fait échouer la mission",
    )

    cree_le = models.DateTimeField(auto_now_add=True, verbose_name="Enregistré le")

    class Meta:
        verbose_name = "Événement de mission"
        verbose_name_plural = "Événements de missions"
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["mission", "timestamp"]),
        ]

    def __str__(self):
        return f"{self.type_evenement.libelle} sur {self.mission.reference}"
