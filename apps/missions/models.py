"""
=============================================================================
Modèles de l'app "missions"
=============================================================================
Cette app modélise le cœur métier : les missions de transport.
  - Mission     : une mission complète (qui transporte quoi, d'où à où, etc.)
  - PositionGPS : trace GPS horodatée du camion durant la mission

Une Mission référence :
  - un Camion (app flotte)
  - un Chauffeur (app flotte)
  - une Ville de départ et une Ville d'arrivée (app geographie)

Pendant son exécution, elle génère :
  - des positions GPS (modèle PositionGPS de cette même app)
  - des événements (app simulation)
  - des dépenses (app finances)
  - un revenu à l'arrivée (app finances)
=============================================================================
"""

from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal


# =============================================================================
# MISSION
# =============================================================================
class Mission(models.Model):
    """
    Une mission de transport : un camion conduit par un chauffeur amène
    une cargaison d'une ville à une autre, contre paiement.
    """

    # ---- Énumérations ----
    class Statut(models.TextChoices):
        """Cycle de vie d'une mission."""
        PLANIFIEE = "planifiee", "Planifiée"
        EN_COURS = "en_cours", "En cours"
        TERMINEE = "terminee", "Terminée avec succès"
        ECHOUEE = "echouee", "Échouée"
        ANNULEE = "annulee", "Annulée"

    class CategorieCargaison(models.TextChoices):
        """Catégories prédéfinies de cargaison transportée."""
        CONTENEUR = "conteneur", "Conteneur"
        CARBURANT = "carburant", "Carburant / Hydrocarbures"
        ALIMENTAIRE = "alimentaire", "Produits alimentaires"
        BETAIL = "betail", "Bétail"
        MATERIAUX = "materiaux", "Matériaux de construction"
        MANUFACTURE = "manufacture", "Produits manufacturés"
        MINERAUX = "mineraux", "Minéraux / Minerais"
        TEXTILE = "textile", "Textile / Vêtements"
        AUTRE = "autre", "Autre"

    # ---- Référence unique ----
    reference = models.CharField(
        max_length=20,
        unique=True,
        blank=True,  # Sera générée automatiquement à la sauvegarde
        verbose_name="Référence",
        help_text="Format : MIS-AAAA-NNNN (généré automatiquement)",
    )

    # ---- Ressources assignées ----
    camion = models.ForeignKey(
        "flotte.Camion",
        on_delete=models.PROTECT,
        related_name="missions",
        verbose_name="Camion",
    )

    chauffeur = models.ForeignKey(
        "flotte.Chauffeur",
        on_delete=models.PROTECT,
        related_name="missions",
        verbose_name="Chauffeur",
    )

    # ---- Trajet ----
    ville_depart = models.ForeignKey(
        "geographie.Ville",
        on_delete=models.PROTECT,
        related_name="missions_au_depart",
        verbose_name="Ville de départ",
    )

    ville_arrivee = models.ForeignKey(
        "geographie.Ville",
        on_delete=models.PROTECT,
        related_name="missions_a_l_arrivee",
        verbose_name="Ville d'arrivée",
    )

    # ---- Cargaison ----
    categorie_cargaison = models.CharField(
        max_length=20,
        choices=CategorieCargaison.choices,
        default=CategorieCargaison.AUTRE,
        verbose_name="Catégorie de cargaison",
    )

    description_cargaison = models.TextField(
        blank=True,
        verbose_name="Description de la cargaison",
        help_text="Détails libres (ex : 18 tonnes de riz blanc en sacs de 50 kg)",
    )

    poids_cargaison_tonnes = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name="Poids de la cargaison (tonnes)",
        validators=[MinValueValidator(Decimal("0"))],
    )

    # ---- Aspect financier ----
    prix_facture_mga = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        verbose_name="Prix facturé au client (Ariary)",
        help_text="Montant brut payé par le client pour la mission",
    )

    nom_client = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Nom du client",
    )

    # ---- Dates ----
    date_creation = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date de création",
    )

    date_depart_prevue = models.DateTimeField(
        verbose_name="Date de départ prévue",
    )

    date_depart_reelle = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date de départ réelle",
    )

    date_arrivee_prevue = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date d'arrivée prévue",
        help_text="Calculée automatiquement depuis la durée des tronçons",
    )

    date_arrivee_reelle = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date d'arrivée réelle",
    )

    # ---- Statut et progression ----
    statut = models.CharField(
        max_length=20,
        choices=Statut.choices,
        default=Statut.PLANIFIEE,
        verbose_name="Statut",
    )

    distance_totale_km = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Distance totale prévue (km)",
        help_text="Calculée depuis les tronçons (départ → arrivée)",
    )

    distance_parcourue_km = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        default=Decimal("0"),
        verbose_name="Distance parcourue (km)",
        help_text="Mise à jour pendant la simulation",
    )

    # ---- Notes libres ----
    notes = models.TextField(
        blank=True,
        verbose_name="Notes",
    )

    class Meta:
        verbose_name = "Mission"
        verbose_name_plural = "Missions"
        # Tri : les plus récentes en premier
        ordering = ["-date_creation"]

    def __str__(self):
        return f"{self.reference} : {self.ville_depart.nom} → {self.ville_arrivee.nom}"

    @property
    def progression_pourcent(self):
        """Renvoie la progression de la mission en pourcentage (0-100)."""
        if not self.distance_totale_km or self.distance_totale_km == 0:
            return 0
        ratio = self.distance_parcourue_km / self.distance_totale_km
        return min(int(ratio * 100), 100)

    def save(self, *args, **kwargs):
        """
        Surcharge de save() pour générer la référence automatiquement
        à la première création (quand l'objet n'a pas encore d'ID).
        """
        if not self.reference:
            from django.utils import timezone
            annee = timezone.now().year
            # On compte les missions déjà créées cette année
            count = Mission.objects.filter(
                date_creation__year=annee
            ).count() + 1
            self.reference = f"MIS-{annee}-{count:04d}"
        super().save(*args, **kwargs)


# =============================================================================
# POSITION GPS
# =============================================================================
class PositionGPS(models.Model):
    """
    Position GPS horodatée d'un camion durant une mission.
    Sert à :
      - rejouer le trajet sur la carte
      - calculer la vitesse moyenne, les arrêts, etc.
      - alimenter le futur module Big Data
    """

    mission = models.ForeignKey(
        Mission,
        on_delete=models.CASCADE,  # Si la mission est supprimée, ses positions aussi
        related_name="positions",
        verbose_name="Mission",
    )

    timestamp = models.DateTimeField(
        verbose_name="Horodatage",
        help_text="Date et heure de la position",
    )

    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        verbose_name="Latitude",
    )

    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        verbose_name="Longitude",
    )

    vitesse_kmh = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0"),
        verbose_name="Vitesse (km/h)",
    )

    distance_parcourue_km = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        default=Decimal("0"),
        verbose_name="Distance parcourue depuis le départ (km)",
    )

    class Meta:
        verbose_name = "Position GPS"
        verbose_name_plural = "Positions GPS"
        # Tri chronologique
        ordering = ["mission", "timestamp"]
        # Index pour accélérer les requêtes "donne-moi toutes les positions
        # d'une mission triées par timestamp"
        indexes = [
            models.Index(fields=["mission", "timestamp"]),
        ]

    def __str__(self):
        return f"{self.mission.reference} @ {self.timestamp:%Y-%m-%d %H:%M}"
