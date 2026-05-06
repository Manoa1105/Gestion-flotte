"""
=============================================================================
Commande : seed_evenements
=============================================================================
Charge le catalogue des types d'événements pouvant survenir durant une mission.

~30 événements réalistes pour le contexte malgache, classés par catégorie :
  - Mécanique     : pannes diverses
  - Trafic        : embouteillages, accidents sur la route
  - Météo         : pluie, cyclone, brouillard, inondations
  - Contrôle      : gendarmerie, douane, pesée
  - Sécurité      : vol, agression, vol de carburant
  - Humain        : fatigue, maladie chauffeur
  - Infrastructure: nids-de-poule, ponts, éboulements
  - Accident      : accrochages, accidents graves

Lancement :
    python manage.py seed_evenements

Cette commande est idempotente (utilise update_or_create).
Tu peux modifier les valeurs ci-dessous et relancer pour mettre à jour.
=============================================================================
"""

from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.simulation.models import TypeEvenement


# =============================================================================
# CATALOGUE DES ÉVÉNEMENTS
# =============================================================================
# Format de chaque événement : dictionnaire avec toutes les valeurs nécessaires.
# Probabilité = chance par HEURE de trajet (0.05 = 5%, 0.001 = 0.1%).
# Coûts en Ariary (devise malgache).

EVENEMENTS = [
    # =========================================================================
    # MÉCANIQUE
    # =========================================================================
    {
        "code": "crevaison",
        "libelle": "Crevaison de pneu",
        "categorie": "mecanique",
        "gravite": "mineure",
        "probabilite_par_heure": 0.0500,
        "duree_min_minutes": 30,
        "duree_max_minutes": 90,
        "cout_min_mga": 50_000,
        "cout_max_mga": 250_000,
        "sensible_etat_route": True,
        "sensible_age_camion": False,
        "peut_faire_echouer_mission": False,
        "description": "Crevaison classique. Probabilité plus élevée sur mauvaises routes.",
    },
    {
        "code": "panne_moteur",
        "libelle": "Panne moteur",
        "categorie": "mecanique",
        "gravite": "grave",
        "probabilite_par_heure": 0.0050,
        "duree_min_minutes": 120,
        "duree_max_minutes": 720,
        "cout_min_mga": 200_000,
        "cout_max_mga": 2_500_000,
        "sensible_etat_route": False,
        "sensible_age_camion": True,
        "peut_faire_echouer_mission": True,
        "description": "Panne moteur. Camions âgés plus à risque. Peut nécessiter remorquage.",
    },
    {
        "code": "surchauffe_moteur",
        "libelle": "Surchauffe moteur",
        "categorie": "mecanique",
        "gravite": "moderee",
        "probabilite_par_heure": 0.0100,
        "duree_min_minutes": 30,
        "duree_max_minutes": 120,
        "cout_min_mga": 0,
        "cout_max_mga": 100_000,
        "sensible_etat_route": False,
        "sensible_age_camion": True,
        "peut_faire_echouer_mission": False,
        "description": "Surchauffe due à la chaleur, forte charge ou montées prolongées.",
    },
    {
        "code": "panne_transmission",
        "libelle": "Panne de transmission",
        "categorie": "mecanique",
        "gravite": "grave",
        "probabilite_par_heure": 0.0030,
        "duree_min_minutes": 240,
        "duree_max_minutes": 720,
        "cout_min_mga": 500_000,
        "cout_max_mga": 3_000_000,
        "sensible_etat_route": True,
        "sensible_age_camion": True,
        "peut_faire_echouer_mission": True,
        "description": "Boîte de vitesse ou embrayage défectueux. Réparation lourde.",
    },
    {
        "code": "panne_freins",
        "libelle": "Problème de freins",
        "categorie": "mecanique",
        "gravite": "grave",
        "probabilite_par_heure": 0.0040,
        "duree_min_minutes": 60,
        "duree_max_minutes": 240,
        "cout_min_mga": 100_000,
        "cout_max_mga": 600_000,
        "sensible_etat_route": False,
        "sensible_age_camion": True,
        "peut_faire_echouer_mission": False,
        "description": "Freins défaillants, plaquettes usées, fuite de liquide.",
    },
    {
        "code": "panne_batterie",
        "libelle": "Panne de batterie",
        "categorie": "mecanique",
        "gravite": "mineure",
        "probabilite_par_heure": 0.0050,
        "duree_min_minutes": 30,
        "duree_max_minutes": 90,
        "cout_min_mga": 50_000,
        "cout_max_mga": 200_000,
        "sensible_etat_route": False,
        "sensible_age_camion": True,
        "peut_faire_echouer_mission": False,
        "description": "Batterie déchargée ou défectueuse.",
    },

    # =========================================================================
    # TRAFIC
    # =========================================================================
    {
        "code": "embouteillage_urbain",
        "libelle": "Embouteillage urbain",
        "categorie": "trafic",
        "gravite": "mineure",
        "probabilite_par_heure": 0.0800,
        "duree_min_minutes": 15,
        "duree_max_minutes": 90,
        "cout_min_mga": 0,
        "cout_max_mga": 0,
        "sensible_etat_route": False,
        "sensible_age_camion": False,
        "peut_faire_echouer_mission": False,
        "description": "Embouteillage classique en zone urbaine (Tana surtout).",
    },
    {
        "code": "travaux_routiers",
        "libelle": "Travaux routiers / Déviation",
        "categorie": "trafic",
        "gravite": "mineure",
        "probabilite_par_heure": 0.0200,
        "duree_min_minutes": 15,
        "duree_max_minutes": 90,
        "cout_min_mga": 0,
        "cout_max_mga": 0,
        "sensible_etat_route": False,
        "sensible_age_camion": False,
        "peut_faire_echouer_mission": False,
        "description": "Chantier en cours, alternat ou déviation.",
    },
    {
        "code": "accident_sur_route",
        "libelle": "Accident sur la route (autre véhicule)",
        "categorie": "trafic",
        "gravite": "moderee",
        "probabilite_par_heure": 0.0100,
        "duree_min_minutes": 30,
        "duree_max_minutes": 240,
        "cout_min_mga": 0,
        "cout_max_mga": 0,
        "sensible_etat_route": True,
        "sensible_age_camion": False,
        "peut_faire_echouer_mission": False,
        "description": "Accident impliquant un autre véhicule, blocage de la route.",
    },

    # =========================================================================
    # MÉTÉO
    # =========================================================================
    {
        "code": "pluie_forte",
        "libelle": "Pluie forte",
        "categorie": "meteo",
        "gravite": "mineure",
        "probabilite_par_heure": 0.0500,
        "duree_min_minutes": 30,
        "duree_max_minutes": 180,
        "cout_min_mga": 0,
        "cout_max_mga": 0,
        "sensible_etat_route": False,
        "sensible_age_camion": False,
        "peut_faire_echouer_mission": False,
        "description": "Pluie forte ralentissant la progression. Plus fréquent saison humide (Nov-Avril).",
    },
    {
        "code": "cyclone",
        "libelle": "Cyclone tropical",
        "categorie": "meteo",
        "gravite": "critique",
        "probabilite_par_heure": 0.0010,
        "duree_min_minutes": 720,
        "duree_max_minutes": 4320,
        "cout_min_mga": 0,
        "cout_max_mga": 5_000_000,
        "sensible_etat_route": False,
        "sensible_age_camion": False,
        "peut_faire_echouer_mission": True,
        "description": "Cyclone tropical (saison Janv-Mars surtout). Mission souvent annulée.",
    },
    {
        "code": "brouillard",
        "libelle": "Brouillard épais",
        "categorie": "meteo",
        "gravite": "mineure",
        "probabilite_par_heure": 0.0150,
        "duree_min_minutes": 30,
        "duree_max_minutes": 120,
        "cout_min_mga": 0,
        "cout_max_mga": 0,
        "sensible_etat_route": False,
        "sensible_age_camion": False,
        "peut_faire_echouer_mission": False,
        "description": "Visibilité réduite, vitesse fortement diminuée. Fréquent zones de cols.",
    },
    {
        "code": "inondation_route",
        "libelle": "Route inondée",
        "categorie": "meteo",
        "gravite": "grave",
        "probabilite_par_heure": 0.0030,
        "duree_min_minutes": 60,
        "duree_max_minutes": 1440,
        "cout_min_mga": 0,
        "cout_max_mga": 100_000,
        "sensible_etat_route": True,
        "sensible_age_camion": False,
        "peut_faire_echouer_mission": True,
        "description": "Route impraticable suite à inondation, attente du retrait des eaux.",
    },

    # =========================================================================
    # CONTRÔLE ADMINISTRATIF
    # =========================================================================
    {
        "code": "controle_gendarmerie",
        "libelle": "Contrôle gendarmerie",
        "categorie": "controle",
        "gravite": "mineure",
        "probabilite_par_heure": 0.0400,
        "duree_min_minutes": 10,
        "duree_max_minutes": 30,
        "cout_min_mga": 0,
        "cout_max_mga": 50_000,
        "sensible_etat_route": False,
        "sensible_age_camion": False,
        "peut_faire_echouer_mission": False,
        "description": "Contrôle de routine sur les routes nationales.",
    },
    {
        "code": "controle_douane",
        "libelle": "Contrôle douane / Poste fiscal",
        "categorie": "controle",
        "gravite": "mineure",
        "probabilite_par_heure": 0.0150,
        "duree_min_minutes": 20,
        "duree_max_minutes": 90,
        "cout_min_mga": 0,
        "cout_max_mga": 200_000,
        "sensible_etat_route": False,
        "sensible_age_camion": False,
        "peut_faire_echouer_mission": False,
        "description": "Contrôle des marchandises et papiers de transport.",
    },
    {
        "code": "controle_papiers",
        "libelle": "Contrôle des papiers du véhicule",
        "categorie": "controle",
        "gravite": "mineure",
        "probabilite_par_heure": 0.0300,
        "duree_min_minutes": 10,
        "duree_max_minutes": 30,
        "cout_min_mga": 0,
        "cout_max_mga": 30_000,
        "sensible_etat_route": False,
        "sensible_age_camion": False,
        "peut_faire_echouer_mission": False,
        "description": "Vérification carte grise, assurance, visite technique, permis.",
    },
    {
        "code": "pesee_routiere",
        "libelle": "Pesée routière",
        "categorie": "controle",
        "gravite": "mineure",
        "probabilite_par_heure": 0.0200,
        "duree_min_minutes": 20,
        "duree_max_minutes": 60,
        "cout_min_mga": 0,
        "cout_max_mga": 200_000,
        "sensible_etat_route": False,
        "sensible_age_camion": False,
        "peut_faire_echouer_mission": False,
        "description": "Pesage du camion, amende possible si surcharge.",
    },

    # =========================================================================
    # SÉCURITÉ
    # =========================================================================
    {
        "code": "tentative_vol_cargaison",
        "libelle": "Tentative de vol de cargaison",
        "categorie": "securite",
        "gravite": "grave",
        "probabilite_par_heure": 0.0030,
        "duree_min_minutes": 30,
        "duree_max_minutes": 180,
        "cout_min_mga": 100_000,
        "cout_max_mga": 5_000_000,
        "sensible_etat_route": False,
        "sensible_age_camion": False,
        "peut_faire_echouer_mission": True,
        "description": "Tentative de braquage, vol partiel ou total de la cargaison.",
    },
    {
        "code": "vol_carburant",
        "libelle": "Vol de carburant",
        "categorie": "securite",
        "gravite": "moderee",
        "probabilite_par_heure": 0.0050,
        "duree_min_minutes": 15,
        "duree_max_minutes": 60,
        "cout_min_mga": 100_000,
        "cout_max_mga": 400_000,
        "sensible_etat_route": False,
        "sensible_age_camion": False,
        "peut_faire_echouer_mission": False,
        "description": "Siphonage de carburant lors d'un arrêt nocturne.",
    },
    {
        "code": "agression_chauffeur",
        "libelle": "Agression du chauffeur",
        "categorie": "securite",
        "gravite": "critique",
        "probabilite_par_heure": 0.0005,
        "duree_min_minutes": 60,
        "duree_max_minutes": 480,
        "cout_min_mga": 50_000,
        "cout_max_mga": 1_000_000,
        "sensible_etat_route": False,
        "sensible_age_camion": False,
        "peut_faire_echouer_mission": True,
        "description": "Agression physique, peut nécessiter hospitalisation.",
    },

    # =========================================================================
    # FACTEUR HUMAIN
    # =========================================================================
    {
        "code": "pause_obligatoire",
        "libelle": "Pause obligatoire (fatigue)",
        "categorie": "humain",
        "gravite": "mineure",
        "probabilite_par_heure": 0.0500,
        "duree_min_minutes": 30,
        "duree_max_minutes": 90,
        "cout_min_mga": 0,
        "cout_max_mga": 30_000,
        "sensible_etat_route": False,
        "sensible_age_camion": False,
        "peut_faire_echouer_mission": False,
        "description": "Pause repas ou repos obligatoire après plusieurs heures de conduite.",
    },
    {
        "code": "maladie_chauffeur",
        "libelle": "Maladie / malaise du chauffeur",
        "categorie": "humain",
        "gravite": "grave",
        "probabilite_par_heure": 0.0020,
        "duree_min_minutes": 120,
        "duree_max_minutes": 1440,
        "cout_min_mga": 50_000,
        "cout_max_mga": 800_000,
        "sensible_etat_route": False,
        "sensible_age_camion": False,
        "peut_faire_echouer_mission": True,
        "description": "Malaise, paludisme, intoxication. Remplacement chauffeur parfois requis.",
    },

    # =========================================================================
    # INFRASTRUCTURE
    # =========================================================================
    {
        "code": "nid_de_poule_majeur",
        "libelle": "Nid-de-poule majeur (dégâts pneu)",
        "categorie": "infrastructure",
        "gravite": "moderee",
        "probabilite_par_heure": 0.0200,
        "duree_min_minutes": 15,
        "duree_max_minutes": 60,
        "cout_min_mga": 50_000,
        "cout_max_mga": 300_000,
        "sensible_etat_route": True,
        "sensible_age_camion": False,
        "peut_faire_echouer_mission": False,
        "description": "Choc important, jante endommagée ou pneu crevé.",
    },
    {
        "code": "pont_fragile",
        "libelle": "Passage de pont fragile",
        "categorie": "infrastructure",
        "gravite": "mineure",
        "probabilite_par_heure": 0.0100,
        "duree_min_minutes": 15,
        "duree_max_minutes": 30,
        "cout_min_mga": 0,
        "cout_max_mga": 0,
        "sensible_etat_route": True,
        "sensible_age_camion": False,
        "peut_faire_echouer_mission": False,
        "description": "Attente que d'autres véhicules passent, traversée prudente.",
    },
    {
        "code": "route_bloquee_eboulement",
        "libelle": "Route bloquée par éboulement",
        "categorie": "infrastructure",
        "gravite": "critique",
        "probabilite_par_heure": 0.0010,
        "duree_min_minutes": 60,
        "duree_max_minutes": 1440,
        "cout_min_mga": 0,
        "cout_max_mga": 0,
        "sensible_etat_route": True,
        "sensible_age_camion": False,
        "peut_faire_echouer_mission": True,
        "description": "Glissement de terrain ou éboulement bloquant complètement la route.",
    },

    # =========================================================================
    # ACCIDENT
    # =========================================================================
    {
        "code": "accrochage_mineur",
        "libelle": "Accrochage mineur",
        "categorie": "accident",
        "gravite": "moderee",
        "probabilite_par_heure": 0.0030,
        "duree_min_minutes": 30,
        "duree_max_minutes": 120,
        "cout_min_mga": 50_000,
        "cout_max_mga": 500_000,
        "sensible_etat_route": False,
        "sensible_age_camion": False,
        "peut_faire_echouer_mission": False,
        "description": "Petit accrochage avec un autre véhicule, constat à faire.",
    },
    {
        "code": "accident_grave",
        "libelle": "Accident grave",
        "categorie": "accident",
        "gravite": "critique",
        "probabilite_par_heure": 0.0005,
        "duree_min_minutes": 240,
        "duree_max_minutes": 1440,
        "cout_min_mga": 1_000_000,
        "cout_max_mga": 10_000_000,
        "sensible_etat_route": True,
        "sensible_age_camion": False,
        "peut_faire_echouer_mission": True,
        "description": "Accident grave : sortie de route, collision sérieuse. Camion immobilisé.",
    },
]


# =============================================================================
# COMMANDE
# =============================================================================
class Command(BaseCommand):
    """Commande Django : python manage.py seed_evenements"""

    help = "Charge le catalogue des types d'événements pouvant survenir durant une mission."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Supprime tous les types d'événements existants avant de re-seeder.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options["reset"]:
            self.stdout.write(self.style.WARNING("Suppression du catalogue existant..."))
            TypeEvenement.objects.all().delete()

        self.stdout.write(self.style.MIGRATE_HEADING("Chargement des types d'événements..."))

        nb_crees = 0
        nb_mis_a_jour = 0
        for ev in EVENEMENTS:
            # update_or_create : crée si absent, met à jour si présent.
            # On identifie un événement par son "code" unique.
            code = ev.pop("code")
            type_ev, cree = TypeEvenement.objects.update_or_create(
                code=code,
                defaults={**ev, "actif": True},
            )
            # On remet le code dans le dict pour le log
            ev["code"] = code
            if cree:
                nb_crees += 1
                symbole = "+"
            else:
                nb_mis_a_jour += 1
                symbole = "~"
            self.stdout.write(
                f"  {symbole} [{type_ev.get_categorie_display():25}] "
                f"{type_ev.libelle} "
                f"(prob/h: {type_ev.probabilite_par_heure})"
            )

        # Résumé
        self.stdout.write(self.style.MIGRATE_HEADING("\n=== Résumé ==="))
        self.stdout.write(f"  Créés          : {nb_crees}")
        self.stdout.write(f"  Mis à jour     : {nb_mis_a_jour}")
        self.stdout.write(f"  Total catalogue: {TypeEvenement.objects.count()}")
        self.stdout.write(self.style.SUCCESS("\nCatalogue d'événements chargé avec succès."))
