"""
=============================================================================
Modèles de l'app "geographie"
=============================================================================
Cette app modélise la géographie physique de Madagascar :
  - Region        : régions administratives (23 régions au total)
  - Ville         : villes avec coordonnées GPS
  - RouteNationale: routes nationales (RN2, RN4, RN7, RN13, etc.)
  - TronconRoute  : segment de route entre deux villes adjacentes

Pourquoi ces modèles ?
Une mission part d'une ville et arrive à une autre. Pour calculer le trajet,
on enchaîne des tronçons. Pour simuler des événements géolocalisés
("contrôle de gendarmerie à Ambatolampy"), il faut une géographie précise.
=============================================================================
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal


# =============================================================================
# REGION
# =============================================================================
class Region(models.Model):
    """
    Région administrative de Madagascar.
    Madagascar compte 23 régions (Analamanga, Atsinanana, Boeny, etc.).
    Une ville appartient à une région.
    """

    nom = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Nom de la région",
        help_text="Exemple : Analamanga, Atsinanana, Boeny",
    )

    code = models.CharField(
        max_length=10,
        unique=True,
        verbose_name="Code de la région",
        help_text="Code court (ex: ANA pour Analamanga)",
    )

    chef_lieu = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Chef-lieu",
        help_text="Ville principale de la région",
    )

    class Meta:
        verbose_name = "Région"
        verbose_name_plural = "Régions"
        ordering = ["nom"]  # Tri alphabétique par défaut

    def __str__(self):
        # Comment cet objet est affiché en texte (admin Django, debug, etc.)
        return self.nom


# =============================================================================
# VILLE
# =============================================================================
class Ville(models.Model):
    """
    Ville de Madagascar avec coordonnées GPS précises.
    Sert d'origine et de destination aux missions, et d'extrémités aux tronçons.
    """

    nom = models.CharField(
        max_length=100,
        verbose_name="Nom de la ville",
    )

    region = models.ForeignKey(
        Region,
        on_delete=models.PROTECT,  # Empêche la suppression d'une région qui a des villes
        related_name="villes",     # On pourra faire region.villes.all()
        verbose_name="Région",
    )

    # Coordonnées GPS - format décimal (DD.dddddd)
    # max_digits=9, decimal_places=6 -> précision d'environ 11 cm
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        validators=[
            MinValueValidator(Decimal("-90")),
            MaxValueValidator(Decimal("90")),
        ],
        verbose_name="Latitude",
        help_text="Entre -90 et 90 (Madagascar : entre -25 et -12)",
    )

    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        validators=[
            MinValueValidator(Decimal("-180")),
            MaxValueValidator(Decimal("180")),
        ],
        verbose_name="Longitude",
        help_text="Entre -180 et 180 (Madagascar : entre 43 et 51)",
    )

    population = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Population",
        help_text="Nombre approximatif d'habitants (optionnel)",
    )

    est_chef_lieu_region = models.BooleanField(
        default=False,
        verbose_name="Chef-lieu de région",
    )

    class Meta:
        verbose_name = "Ville"
        verbose_name_plural = "Villes"
        ordering = ["nom"]
        # Empêche d'avoir deux fois la même ville dans la même région
        unique_together = [["nom", "region"]]

    def __str__(self):
        return f"{self.nom} ({self.region.code})"


# =============================================================================
# ROUTE NATIONALE
# =============================================================================
class RouteNationale(models.Model):
    """
    Route nationale de Madagascar (RN1, RN2, RN4, RN7, RN13, etc.).
    Une route nationale relie plusieurs villes via une suite de tronçons.
    """

    numero = models.CharField(
        max_length=10,
        unique=True,
        verbose_name="Numéro",
        help_text="Exemple : RN2, RN4, RN7, RN13",
    )

    nom_long = models.CharField(
        max_length=200,
        verbose_name="Nom complet",
        help_text="Exemple : Antananarivo - Toamasina",
    )

    longueur_totale_km = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Longueur totale (km)",
        help_text="Calculée depuis les tronçons (peut être laissée vide)",
    )

    description = models.TextField(
        blank=True,
        verbose_name="Description",
        help_text="État général, particularités, zones difficiles, etc.",
    )

    class Meta:
        verbose_name = "Route nationale"
        verbose_name_plural = "Routes nationales"
        ordering = ["numero"]

    def __str__(self):
        return f"{self.numero} ({self.nom_long})"


# =============================================================================
# TRONÇON DE ROUTE
# =============================================================================
class TronconRoute(models.Model):
    """
    Segment de route entre deux villes ADJACENTES sur une route nationale.

    Exemple : Antananarivo - Antsirabe sur la RN7 = un tronçon.
              Antsirabe - Ambositra sur la RN7 = un autre tronçon.

    Pour aller de Antananarivo à Fianarantsoa, on enchaîne plusieurs tronçons.

    Cette granularité permet :
      - de calculer précisément la distance d'une mission
      - de placer des événements à un endroit précis du trajet
      - de modéliser que certaines portions sont en mauvais état
    """

    # Les 4 valeurs possibles pour l'état d'une route, comme une "enum"
    class EtatRoute(models.TextChoices):
        EXCELLENT = "excellent", "Excellent (asphalte neuf)"
        BON = "bon", "Bon"
        MOYEN = "moyen", "Moyen (quelques nids-de-poule)"
        MAUVAIS = "mauvais", "Mauvais (nombreux trous)"
        TRES_MAUVAIS = "tres_mauvais", "Très mauvais (piste dégradée)"

    route = models.ForeignKey(
        RouteNationale,
        on_delete=models.CASCADE,  # Si on supprime la route, ses tronçons disparaissent
        related_name="troncons",
        verbose_name="Route nationale",
    )

    # related_name différent pour ville_depart et ville_arrivee
    # car les deux pointent sur le même modèle Ville
    ville_depart = models.ForeignKey(
        Ville,
        on_delete=models.PROTECT,
        related_name="troncons_au_depart",
        verbose_name="Ville de départ du tronçon",
    )

    ville_arrivee = models.ForeignKey(
        Ville,
        on_delete=models.PROTECT,
        related_name="troncons_a_l_arrivee",
        verbose_name="Ville d'arrivée du tronçon",
    )

    distance_km = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        verbose_name="Distance (km)",
    )

    duree_typique_minutes = models.PositiveIntegerField(
        verbose_name="Durée typique (minutes)",
        help_text="Temps moyen de parcours pour un camion semi-remorque chargé",
    )

    etat_route = models.CharField(
        max_length=20,
        choices=EtatRoute.choices,
        default=EtatRoute.MOYEN,
        verbose_name="État de la route",
    )

    description = models.TextField(
        blank=True,
        verbose_name="Notes",
        help_text="Particularités : zones de cols, ponts, zones à risque, etc.",
    )

    # ----- Polyline réelle (suit la vraie route, pas la ligne droite) -----
    polyline_geojson = models.JSONField(
        null=True,
        blank=True,
        verbose_name="Polyline réelle (GeoJSON LineString)",
        help_text=(
            "Suite de coordonnées GPS [lon, lat] qui suit la vraie route. "
            "Téléchargée via OSRM (OpenStreetMap). "
            "Si vide, l'app dessine une ligne droite entre les villes."
        ),
    )

    class Meta:
        verbose_name = "Tronçon de route"
        verbose_name_plural = "Tronçons de route"
        ordering = ["route__numero", "ville_depart__nom"]
        unique_together = [["route", "ville_depart", "ville_arrivee"]]

    def __str__(self):
        return f"{self.route.numero} : {self.ville_depart.nom} → {self.ville_arrivee.nom} ({self.distance_km} km)"

    @property
    def polyline_latlon(self):
        """Renvoie la polyline au format [(lat, lon), ...]."""
        if self.polyline_geojson and "coordinates" in self.polyline_geojson:
            return [(c[1], c[0]) for c in self.polyline_geojson["coordinates"]]
        return [
            (float(self.ville_depart.latitude), float(self.ville_depart.longitude)),
            (float(self.ville_arrivee.latitude), float(self.ville_arrivee.longitude)),
        ]
