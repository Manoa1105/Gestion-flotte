"""
=============================================================================
Modèles de l'app "flotte"
=============================================================================
Cette app modélise les ressources humaines et matérielles de l'entreprise :
  - Camion    : véhicules semi-remorques de la flotte
  - Chauffeur : personnel de conduite

Le choix de séparer ces deux modèles (sans lien permanent entre eux) permet
qu'un chauffeur puisse conduire différents camions selon les missions.
=============================================================================
"""

from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal


# =============================================================================
# CAMION
# =============================================================================
class Camion(models.Model):
    """
    Camion semi-remorque de la flotte.
    Chaque camion possède son propre statut (disponible, en mission, en panne...).
    """

    # ---- Énumérations ----
    class Statut(models.TextChoices):
        """États possibles d'un camion à un instant donné."""
        DISPONIBLE = "disponible", "Disponible"
        EN_MISSION = "en_mission", "En mission"
        EN_PANNE = "en_panne", "En panne"
        EN_MAINTENANCE = "en_maintenance", "En maintenance"
        HORS_SERVICE = "hors_service", "Hors service"

    # ---- Identification ----
    immatriculation = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Immatriculation",
        help_text="Numéro d'immatriculation officiel (ex : 1234 TBC)",
    )

    marque = models.CharField(
        max_length=50,
        verbose_name="Marque",
        help_text="Mercedes, Volvo, Scania, Renault Trucks, etc.",
    )

    modele = models.CharField(
        max_length=50,
        verbose_name="Modèle",
        help_text="Exemple : Actros, FH16, R450",
    )

    annee_fabrication = models.PositiveIntegerField(
        verbose_name="Année de fabrication",
        validators=[MinValueValidator(1980)],
    )

    # ---- Caractéristiques techniques ----
    capacite_charge_tonnes = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name="Capacité de charge (tonnes)",
        help_text="Charge utile maximale (ex : 25.00)",
    )

    consommation_litres_100km = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        verbose_name="Consommation (L/100 km)",
        help_text="Consommation moyenne à charge normale",
    )

    kilometrage_total = models.PositiveIntegerField(
        default=0,
        verbose_name="Kilométrage total",
        help_text="Mis à jour automatiquement à la fin de chaque mission",
    )

    # ---- Données financières d'acquisition ----
    date_acquisition = models.DateField(
        verbose_name="Date d'acquisition",
    )

    prix_acquisition_mga = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        verbose_name="Prix d'acquisition (Ariary)",
        help_text="Prix d'achat du camion en Ariary",
    )

    # ---- État opérationnel ----
    statut = models.CharField(
        max_length=20,
        choices=Statut.choices,
        default=Statut.DISPONIBLE,
        verbose_name="Statut",
    )

    # ---- Métadonnées ----
    photo = models.ImageField(
        upload_to="camions/",
        null=True,
        blank=True,
        verbose_name="Photo du camion",
    )

    notes = models.TextField(
        blank=True,
        verbose_name="Notes",
        help_text="Particularités, historique des réparations majeures, etc.",
    )

    cree_le = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Créé le",
    )

    modifie_le = models.DateTimeField(
        auto_now=True,
        verbose_name="Modifié le",
    )

    class Meta:
        verbose_name = "Camion"
        verbose_name_plural = "Camions"
        ordering = ["immatriculation"]

    def __str__(self):
        return f"{self.immatriculation} - {self.marque} {self.modele}"

    @property
    def description_courte(self):
        """Renvoie une description compacte du camion (utile dans les listes)."""
        return f"{self.marque} {self.modele} ({self.immatriculation})"


# =============================================================================
# CHAUFFEUR
# =============================================================================
class Chauffeur(models.Model):
    """
    Chauffeur de l'entreprise.
    Chaque mission doit être assignée à un chauffeur disponible.
    """

    # ---- Énumérations ----
    class Statut(models.TextChoices):
        """États possibles d'un chauffeur."""
        DISPONIBLE = "disponible", "Disponible"
        EN_MISSION = "en_mission", "En mission"
        REPOS = "repos", "En repos"
        CONGE = "conge", "En congé"
        INACTIF = "inactif", "Inactif (a quitté l'entreprise)"

    class TypePermis(models.TextChoices):
        """Catégories de permis de conduire malgaches utiles ici."""
        CE = "CE", "CE (poids lourds + remorque)"
        D = "D", "D (transport de personnes)"
        C = "C", "C (poids lourds)"

    # ---- Identité ----
    nom = models.CharField(
        max_length=100,
        verbose_name="Nom",
    )

    prenom = models.CharField(
        max_length=100,
        verbose_name="Prénom",
    )

    date_naissance = models.DateField(
        null=True,
        blank=True,
        verbose_name="Date de naissance",
    )

    telephone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name="Téléphone",
        help_text="Format malgache : +261 32 12 345 67",
    )

    email = models.EmailField(
        blank=True,
        verbose_name="Email",
    )

    # ---- Permis et expérience ----
    numero_permis = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Numéro de permis",
    )

    type_permis = models.CharField(
        max_length=5,
        choices=TypePermis.choices,
        default=TypePermis.CE,
        verbose_name="Type de permis",
    )

    annees_experience = models.PositiveIntegerField(
        default=0,
        verbose_name="Années d'expérience",
        help_text="Expérience cumulée en conduite poids lourds",
    )

    # ---- Données contractuelles ----
    date_embauche = models.DateField(
        verbose_name="Date d'embauche",
    )

    salaire_mensuel_mga = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Salaire mensuel (Ariary)",
        validators=[MinValueValidator(Decimal("0"))],
    )

    # ---- État opérationnel ----
    statut = models.CharField(
        max_length=20,
        choices=Statut.choices,
        default=Statut.DISPONIBLE,
        verbose_name="Statut",
    )

    notes = models.TextField(
        blank=True,
        verbose_name="Notes",
    )

    cree_le = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    modifie_le = models.DateTimeField(auto_now=True, verbose_name="Modifié le")

    class Meta:
        verbose_name = "Chauffeur"
        verbose_name_plural = "Chauffeurs"
        ordering = ["nom", "prenom"]

    def __str__(self):
        return f"{self.prenom} {self.nom}"

    @property
    def nom_complet(self):
        """Renvoie le nom complet, utile dans les templates."""
        return f"{self.prenom} {self.nom}"
