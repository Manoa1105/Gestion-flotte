"""
=============================================================================
Commande : seed_finances
=============================================================================
Charge le catalogue des types de dépenses possibles dans l'entreprise.

~20 types de dépenses classés par grande catégorie :
  - Opérationnelle    : carburant, péage, frais de route
  - RH                : salaires, primes, indemnités
  - Maintenance       : vidange, pneus, réparations
  - Administrative    : taxes, amendes, frais de douane
  - Assurance         : assurance véhicule et cargaison

Lancement :
    python manage.py seed_finances
=============================================================================
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.finances.models import TypeDepense


# =============================================================================
# CATALOGUE DES TYPES DE DÉPENSES
# =============================================================================
# Tuple (code, libellé, catégorie, description)

TYPES_DEPENSES = [
    # ----- Opérationnelles (liées à l'exécution des missions) -----
    ("carburant", "Carburant (gazole / essence)", "operationnelle",
     "Achat de carburant pendant une mission. Calculé automatiquement par la simulation."),
    ("peage", "Péage routier", "operationnelle",
     "Frais de péage sur les routes payantes."),
    ("repas_chauffeur", "Repas chauffeur en mission", "operationnelle",
     "Indemnité repas pendant les longues missions."),
    ("hebergement_chauffeur", "Hébergement chauffeur", "operationnelle",
     "Hôtel ou logement lors des missions de plusieurs jours."),

    # ----- Ressources humaines -----
    ("salaire_chauffeur", "Salaire mensuel chauffeur", "rh",
     "Versement mensuel du salaire du chauffeur."),
    ("salaire_administratif", "Salaire personnel administratif", "rh",
     "Salaires des employés non-chauffeurs (gestionnaires, comptables, etc.)."),
    ("prime_mission", "Prime de mission réussie", "rh",
     "Prime versée au chauffeur après une mission réussie sans incident majeur."),
    ("formation", "Formation du personnel", "rh",
     "Stages de conduite défensive, recyclage permis, formations sécurité."),

    # ----- Maintenance -----
    ("vidange", "Vidange et entretien périodique", "maintenance",
     "Vidange moteur, filtres, entretien de routine."),
    ("reparation_pneu", "Réparation / remplacement pneu", "maintenance",
     "Réparation après crevaison, remplacement de pneus usés."),
    ("reparation_moteur", "Réparation moteur", "maintenance",
     "Toute intervention mécanique sur le moteur."),
    ("reparation_transmission", "Réparation transmission", "maintenance",
     "Boîte de vitesse, embrayage, arbres de transmission."),
    ("reparation_carrosserie", "Réparation carrosserie", "maintenance",
     "Suite à accrochage, accident, ou dégradation."),
    ("piece_detachee", "Achat de pièces détachées", "maintenance",
     "Pièces stockées en prévision (filtres, courroies, etc.)."),
    ("controle_technique", "Contrôle technique", "maintenance",
     "Visite technique obligatoire."),

    # ----- Administrative -----
    ("amende", "Amende routière", "administrative",
     "Amende suite à un contrôle (excès de vitesse, surcharge, papiers manquants)."),
    ("frais_douane", "Frais de douane / poste fiscal", "administrative",
     "Frais administratifs aux postes de contrôle douanier."),
    ("taxe_routiere", "Taxe routière / vignette", "administrative",
     "Taxes annuelles sur les véhicules."),
    ("frais_administratif", "Frais administratif divers", "administrative",
     "Photocopies, timbres, déclarations, dossiers."),

    # ----- Assurance -----
    ("assurance_vehicule", "Assurance véhicule (annuelle)", "assurance",
     "Prime annuelle d'assurance du camion."),
    ("assurance_cargaison", "Assurance cargaison", "assurance",
     "Assurance pour la cargaison transportée, par mission ou globale."),
]


# =============================================================================
# COMMANDE
# =============================================================================
class Command(BaseCommand):
    """Commande Django : python manage.py seed_finances"""

    help = "Charge le catalogue des types de dépenses."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Supprime tous les types de dépenses existants avant de re-seeder.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options["reset"]:
            self.stdout.write(self.style.WARNING("Suppression du catalogue existant..."))
            TypeDepense.objects.all().delete()

        self.stdout.write(self.style.MIGRATE_HEADING("Chargement des types de dépenses..."))

        nb_crees = 0
        nb_mis_a_jour = 0
        for code, libelle, categorie, description in TYPES_DEPENSES:
            type_dep, cree = TypeDepense.objects.update_or_create(
                code=code,
                defaults={
                    "libelle": libelle,
                    "categorie": categorie,
                    "description": description,
                    "actif": True,
                },
            )
            symbole = "+" if cree else "~"
            if cree:
                nb_crees += 1
            else:
                nb_mis_a_jour += 1
            self.stdout.write(
                f"  {symbole} [{type_dep.get_categorie_display():25}] {type_dep.libelle}"
            )

        self.stdout.write(self.style.MIGRATE_HEADING("\n=== Résumé ==="))
        self.stdout.write(f"  Créés          : {nb_crees}")
        self.stdout.write(f"  Mis à jour     : {nb_mis_a_jour}")
        self.stdout.write(f"  Total catalogue: {TypeDepense.objects.count()}")
        self.stdout.write(self.style.SUCCESS("\nCatalogue de dépenses chargé avec succès."))
