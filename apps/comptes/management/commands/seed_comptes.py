"""
=============================================================================
Commande : seed_comptes
=============================================================================
Crée les comptes utilisateurs de démonstration :

  gestionnaire / Gestionnaire123  → accès complet
  comptable    / Comptable123     → finances + missions (lecture)
  chauffeur1   / Chauffeur123     → ses propres missions

Lancement :
    python manage.py seed_comptes

Si les comptes existent déjà, la commande ne fait rien (idempotente).
=============================================================================
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from apps.comptes.models import ProfilUtilisateur


class Command(BaseCommand):
    help = "Crée les comptes utilisateurs de démonstration."

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING("Création des comptes de démonstration..."))

        comptes = [
            {
                "username": "gestionnaire",
                "password": "Gestionnaire123",
                "first_name": "Marie",
                "last_name": "Rakoto",
                "role": ProfilUtilisateur.Role.GESTIONNAIRE,
                "description": "accès complet à toutes les sections",
            },
            {
                "username": "comptable",
                "password": "Comptable123",
                "first_name": "Jean",
                "last_name": "Razafy",
                "role": ProfilUtilisateur.Role.COMPTABLE,
                "description": "finances + tableau de bord + missions (lecture seule)",
            },
            {
                "username": "chauffeur1",
                "password": "Chauffeur123",
                "first_name": "Paul",
                "last_name": "Andria",
                "role": ProfilUtilisateur.Role.CHAUFFEUR,
                "description": "tableau de bord + ses propres missions",
            },
        ]

        nb_crees = 0
        for data in comptes:
            if User.objects.filter(username=data["username"]).exists():
                self.stdout.write(
                    f"  • {data['username']} : déjà existant, ignoré."
                )
                continue

            user = User.objects.create_user(
                username=data["username"],
                password=data["password"],
                first_name=data["first_name"],
                last_name=data["last_name"],
            )
            ProfilUtilisateur.objects.create(
                utilisateur=user,
                role=data["role"],
            )
            self.stdout.write(self.style.SUCCESS(
                f"  • {data['username']} créé ({data['description']})"
            ))
            nb_crees += 1

        self.stdout.write("")
        if nb_crees > 0:
            self.stdout.write(self.style.SUCCESS(f"{nb_crees} compte(s) créé(s)."))
            self.stdout.write("")
            self.stdout.write("  Identifiants de connexion :")
            self.stdout.write("  ┌────────────────┬──────────────────┬──────────────────────┐")
            self.stdout.write("  │ Utilisateur    │ Mot de passe     │ Rôle                 │")
            self.stdout.write("  ├────────────────┼──────────────────┼──────────────────────┤")
            self.stdout.write("  │ gestionnaire   │ Gestionnaire123  │ Gestionnaire         │")
            self.stdout.write("  │ comptable      │ Comptable123     │ Comptable            │")
            self.stdout.write("  │ chauffeur1     │ Chauffeur123     │ Chauffeur            │")
            self.stdout.write("  └────────────────┴──────────────────┴──────────────────────┘")
        else:
            self.stdout.write("Tous les comptes existaient déjà, rien à créer.")
