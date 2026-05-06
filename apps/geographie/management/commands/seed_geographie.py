"""
=============================================================================
Commande : seed_geographie
=============================================================================
Charge dans la base de données la géographie de Madagascar :
  - 23 régions administratives
  - ~30 villes principales avec coordonnées GPS réelles
  - 10 routes nationales (RN1, RN2, RN4, RN6, RN7, RN13, etc.)
  - ~25 tronçons entre villes adjacentes avec distances et durées réalistes

Lancement :
    python manage.py seed_geographie

Cette commande est IDEMPOTENTE : on peut la relancer plusieurs fois,
elle ne créera pas de doublons (utilisation de get_or_create).

Source des données :
  - Découpage administratif officiel de Madagascar (23 régions)
  - Coordonnées GPS : Wikipedia, OpenStreetMap
  - Distances et durées : approximations réalistes pour un semi-remorque chargé
=============================================================================
"""

from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.geographie.models import Region, Ville, RouteNationale, TronconRoute


# =============================================================================
# DONNÉES : RÉGIONS DE MADAGASCAR
# =============================================================================
# Tuple (code, nom, chef-lieu)
# Madagascar compte 23 régions depuis la subdivision Vatovavy-Fitovinany en 2021.
REGIONS = [
    ("ANA", "Analamanga", "Antananarivo"),
    ("VAK", "Vakinankaratra", "Antsirabe"),
    ("ITA", "Itasy", "Miarinarivo"),
    ("BON", "Bongolava", "Tsiroanomandidy"),
    ("SOF", "Sofia", "Antsohihy"),
    ("BOE", "Boeny", "Mahajanga"),
    ("BET", "Betsiboka", "Maevatanana"),
    ("MEL", "Melaky", "Maintirano"),
    ("ALA", "Alaotra-Mangoro", "Ambatondrazaka"),
    ("ATS", "Atsinanana", "Toamasina"),
    ("ANJ", "Analanjirofo", "Fenoarivo Atsinanana"),
    ("AMM", "Amoron'i Mania", "Ambositra"),
    ("VAT", "Vatovavy", "Mananjary"),
    ("FIT", "Fitovinany", "Manakara"),
    ("HMA", "Haute Matsiatra", "Fianarantsoa"),
    ("ATA", "Atsimo-Atsinanana", "Farafangana"),
    ("IHO", "Ihorombe", "Ihosy"),
    ("MEN", "Menabe", "Morondava"),
    ("AAN", "Atsimo-Andrefana", "Toliara"),
    ("AND", "Androy", "Ambovombe"),
    ("ANO", "Anosy", "Tolagnaro"),
    ("SAV", "SAVA", "Sambava"),
    ("DIA", "Diana", "Antsiranana"),
]


# =============================================================================
# DONNÉES : VILLES PRINCIPALES
# =============================================================================
# Tuple (nom, code_region, latitude, longitude, population, est_chef_lieu)
# Coordonnées GPS au format décimal, négatives pour latitude (hémisphère sud).
VILLES = [
    # --- Hauts plateaux centraux ---
    ("Antananarivo",  "ANA", -18.879190, 47.507905, 1300000, True),
    ("Antsirabe",     "VAK", -19.866667, 47.033333,  265000, True),
    ("Ambatolampy",   "VAK", -19.383333, 47.433333,   30000, False),
    ("Ambositra",     "AMM", -20.531111, 47.246944,   30000, True),
    ("Fianarantsoa",  "HMA", -21.453611, 47.085556,  170000, True),
    ("Miarinarivo",   "ITA", -19.000000, 46.850000,   20000, True),
    ("Tsiroanomandidy","BON", -18.766667, 46.050000,   28000, True),
    ("Moramanga",     "ALA", -18.933333, 48.200000,   40000, False),
    ("Ambatondrazaka","ALA", -17.833333, 48.416667,   55000, True),

    # --- Côte est ---
    ("Toamasina",     "ATS", -18.149200, 49.402300,  300000, True),
    ("Vatomandry",    "ATS", -19.333333, 48.983333,   25000, False),
    ("Fenoarivo Atsinanana", "ANJ", -17.383333, 49.400000, 25000, True),
    ("Mananjary",     "VAT", -21.230000, 48.341700,   42000, True),
    ("Manakara",      "FIT", -22.145300, 48.012500,   45000, True),
    ("Farafangana",   "ATA", -22.816667, 47.833333,   35000, True),

    # --- Sud ---
    ("Ihosy",         "IHO", -22.401700, 46.123300,   30000, True),
    ("Toliara",       "AAN", -23.350000, 43.666667,  170000, True),
    ("Ambovombe",     "AND", -25.166667, 46.083333,   65000, True),
    ("Tolagnaro",     "ANO", -25.031400, 46.998100,   60000, True),

    # --- Côte ouest ---
    ("Morondava",     "MEN", -20.284100, 44.281000,   45000, True),
    ("Maintirano",    "MEL", -18.050000, 44.016700,   12000, True),

    # --- Nord-ouest ---
    ("Mahajanga",     "BOE", -15.716700, 46.316700,  220000, True),
    ("Maevatanana",   "BET", -16.950000, 46.833333,   25000, True),
    ("Antsohihy",     "SOF", -14.883333, 47.983333,   25000, True),
    ("Ambato Boeny",  "BOE", -16.466700, 46.716700,   15000, False),

    # --- Nord ---
    ("Antsiranana",   "DIA", -12.278700, 49.291700,  115000, True),
    ("Ambanja",       "DIA", -13.683333, 48.450000,   30000, False),
    ("Sambava",       "SAV", -14.266667, 50.166667,   60000, True),
    ("Antalaha",      "SAV", -14.900000, 50.283333,   45000, False),
]


# =============================================================================
# DONNÉES : ROUTES NATIONALES
# =============================================================================
# Tuple (numéro, nom_long, description)
ROUTES = [
    ("RN1",  "Antananarivo - Tsiroanomandidy",
     "Axe ouest depuis la capitale, vers Tsiroanomandidy puis Maintirano (côte ouest)."),
    ("RN2",  "Antananarivo - Toamasina",
     "Axe principal vers le port de Toamasina (1er port de Madagascar). Trafic dense."),
    ("RN4",  "Antananarivo - Mahajanga",
     "Axe vers le nord-ouest et le port de Mahajanga. Longue traversée."),
    ("RN5",  "Toamasina - Maroantsetra",
     "Côte est vers le nord. État souvent dégradé, parfois impraticable en saison des pluies."),
    ("RN6",  "Antananarivo - Antsiranana",
     "Axe nord depuis Antananarivo via la RN4 puis bifurcation. Très long (~1100 km)."),
    ("RN7",  "Antananarivo - Toliara",
     "Axe principal sud, l'une des routes les plus utilisées. ~960 km."),
    ("RN8",  "Toliara - Morondava",
     "Côte ouest, axe sud vers Morondava."),
    ("RN10", "Ihosy - Tolagnaro",
     "Axe sud vers Fort-Dauphin, longue traversée du grand sud aride."),
    ("RN13", "Ihosy - Ambovombe - Tolagnaro",
     "Liaison sud par l'intérieur, état très variable, partie sud très dégradée."),
    ("RN44", "Moramanga - Ambatondrazaka",
     "Liaison vers le lac Alaotra, principale région rizicole."),
]


# =============================================================================
# DONNÉES : TRONÇONS DE ROUTE
# =============================================================================
# Tuple (route, ville_depart, ville_arrivee, distance_km, duree_min, etat)
# États possibles : excellent, bon, moyen, mauvais, tres_mauvais
# Durées calibrées pour un semi-remorque chargé, pas une voiture.
TRONCONS = [
    # --- RN2 : Tana - Toamasina ---
    ("RN2", "Antananarivo", "Moramanga",         110, 150, "moyen"),
    ("RN2", "Moramanga",    "Toamasina",         260, 300, "moyen"),

    # --- RN4 : Tana - Mahajanga ---
    ("RN4", "Antananarivo", "Maevatanana",       320, 360, "bon"),
    ("RN4", "Maevatanana",  "Ambato Boeny",       80,  90, "bon"),
    ("RN4", "Ambato Boeny", "Mahajanga",         170, 180, "bon"),

    # --- RN7 : Tana - Toliara (l'axe sud le plus important) ---
    ("RN7", "Antananarivo", "Ambatolampy",        65,  90, "bon"),
    ("RN7", "Ambatolampy",  "Antsirabe",         105, 120, "bon"),
    ("RN7", "Antsirabe",    "Ambositra",         100, 120, "moyen"),
    ("RN7", "Ambositra",    "Fianarantsoa",      140, 150, "moyen"),
    ("RN7", "Fianarantsoa", "Ihosy",             200, 240, "moyen"),
    ("RN7", "Ihosy",        "Toliara",           360, 420, "mauvais"),

    # --- RN6 : axe nord (vers Diego-Suarez) ---
    ("RN6", "Antsohihy",    "Ambanja",           200, 300, "mauvais"),
    ("RN6", "Ambanja",      "Antsiranana",       240, 300, "moyen"),
    ("RN6", "Maevatanana",  "Antsohihy",         380, 600, "tres_mauvais"),

    # --- RN13 : axe sud-est (Ihosy - Fort-Dauphin) ---
    ("RN13","Ihosy",        "Ambovombe",         350, 540, "tres_mauvais"),
    ("RN13","Ambovombe",    "Tolagnaro",         110, 180, "mauvais"),

    # --- RN44 : vers le lac Alaotra ---
    ("RN44","Moramanga",    "Ambatondrazaka",    180, 240, "moyen"),

    # --- RN5 : côte est nord ---
    ("RN5", "Toamasina",    "Fenoarivo Atsinanana", 100, 180, "mauvais"),

    # --- RN1 : axe ouest ---
    ("RN1", "Antananarivo", "Tsiroanomandidy",   220, 270, "moyen"),

    # --- RN8 : Toliara - Morondava (côte ouest) ---
    ("RN8", "Toliara",      "Morondava",         500, 720, "tres_mauvais"),

    # --- Liaisons côte est sud ---
    ("RN7", "Fianarantsoa", "Manakara",          250, 360, "mauvais"),
    ("RN7", "Manakara",     "Mananjary",          90, 150, "mauvais"),
    ("RN7", "Manakara",     "Farafangana",       110, 180, "mauvais"),
]


# =============================================================================
# COMMANDE
# =============================================================================
class Command(BaseCommand):
    """Commande Django : python manage.py seed_geographie"""

    # Description affichée par "python manage.py help seed_geographie"
    help = "Charge dans la base les régions, villes, routes nationales et tronçons de Madagascar."

    def add_arguments(self, parser):
        """Définit les options de ligne de commande acceptées."""
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Supprime toutes les données existantes avant de re-seeder.",
        )

    @transaction.atomic  # Tout ou rien : si une erreur survient, aucun changement n'est sauvé
    def handle(self, *args, **options):
        """Point d'entrée de la commande."""
        if options["reset"]:
            self.stdout.write(self.style.WARNING("Suppression des données existantes..."))
            TronconRoute.objects.all().delete()
            RouteNationale.objects.all().delete()
            Ville.objects.all().delete()
            Region.objects.all().delete()

        # ---- 1. Régions ----
        self.stdout.write(self.style.MIGRATE_HEADING("Chargement des régions..."))
        regions_par_code = {}  # On garde un index pour retrouver une région par son code
        for code, nom, chef_lieu in REGIONS:
            region, cree = Region.objects.get_or_create(
                code=code,
                defaults={"nom": nom, "chef_lieu": chef_lieu},
            )
            regions_par_code[code] = region
            symbole = "+" if cree else "="
            self.stdout.write(f"  {symbole} {region.nom} ({code})")
        self.stdout.write(self.style.SUCCESS(f"{len(REGIONS)} régions traitées."))

        # ---- 2. Villes ----
        self.stdout.write(self.style.MIGRATE_HEADING("\nChargement des villes..."))
        villes_par_nom = {}
        for nom, code_region, lat, lon, pop, est_chef in VILLES:
            ville, cree = Ville.objects.get_or_create(
                nom=nom,
                region=regions_par_code[code_region],
                defaults={
                    "latitude": Decimal(str(lat)),
                    "longitude": Decimal(str(lon)),
                    "population": pop,
                    "est_chef_lieu_region": est_chef,
                },
            )
            villes_par_nom[nom] = ville
            symbole = "+" if cree else "="
            self.stdout.write(f"  {symbole} {ville.nom} ({code_region})")
        self.stdout.write(self.style.SUCCESS(f"{len(VILLES)} villes traitées."))

        # ---- 3. Routes nationales ----
        self.stdout.write(self.style.MIGRATE_HEADING("\nChargement des routes nationales..."))
        routes_par_numero = {}
        for numero, nom_long, description in ROUTES:
            route, cree = RouteNationale.objects.get_or_create(
                numero=numero,
                defaults={"nom_long": nom_long, "description": description},
            )
            routes_par_numero[numero] = route
            symbole = "+" if cree else "="
            self.stdout.write(f"  {symbole} {route.numero} : {route.nom_long}")
        self.stdout.write(self.style.SUCCESS(f"{len(ROUTES)} routes traitées."))

        # ---- 4. Tronçons ----
        self.stdout.write(self.style.MIGRATE_HEADING("\nChargement des tronçons..."))
        nb_crees = 0
        nb_existants = 0
        for numero_route, nom_dep, nom_arr, distance, duree, etat in TRONCONS:
            # Récupération des objets liés
            route = routes_par_numero.get(numero_route)
            ville_dep = villes_par_nom.get(nom_dep)
            ville_arr = villes_par_nom.get(nom_arr)

            # Sécurité : si une référence est introuvable, on signale et on saute
            if not (route and ville_dep and ville_arr):
                self.stdout.write(self.style.ERROR(
                    f"  ! Tronçon {nom_dep} -> {nom_arr} ignoré (référence manquante)"
                ))
                continue

            troncon, cree = TronconRoute.objects.get_or_create(
                route=route,
                ville_depart=ville_dep,
                ville_arrivee=ville_arr,
                defaults={
                    "distance_km": Decimal(str(distance)),
                    "duree_typique_minutes": duree,
                    "etat_route": etat,
                },
            )
            if cree:
                nb_crees += 1
                self.stdout.write(f"  + {troncon}")
            else:
                nb_existants += 1

        self.stdout.write(self.style.SUCCESS(
            f"{nb_crees} tronçons créés, {nb_existants} déjà existants."
        ))

        # ---- Résumé final ----
        self.stdout.write(self.style.MIGRATE_HEADING("\n=== Résumé ==="))
        self.stdout.write(f"  Régions       : {Region.objects.count()}")
        self.stdout.write(f"  Villes        : {Ville.objects.count()}")
        self.stdout.write(f"  Routes        : {RouteNationale.objects.count()}")
        self.stdout.write(f"  Tronçons      : {TronconRoute.objects.count()}")
        self.stdout.write(self.style.SUCCESS("\nGéographie chargée avec succès."))
