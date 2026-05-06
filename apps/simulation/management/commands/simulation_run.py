"""
=============================================================================
Commande : simulation_run
=============================================================================
Boucle infinie qui fait avancer toutes les missions en cours.

Usage :
    python manage.py simulation_run
    python manage.py simulation_run --vitesse 60 --intervalle 1
    python manage.py simulation_run --vitesse 600 --intervalle 1   # tres rapide

Parametres :
    --vitesse    : facteur d'acceleration (defaut 60)
                   60 = 1 seconde reelle = 60 secondes simulees (1 minute)
                   600 = 1 seconde reelle = 10 minutes simulees (genere bcp de donnees)
    --intervalle : delai entre 2 ticks en secondes (defaut 1.0)

Pour arreter : Ctrl+C dans le terminal.
=============================================================================
"""

import time
import signal
import sys

from django.core.management.base import BaseCommand
from apps.missions.models import Mission
from apps.simulation.services import avancer_mission


class Command(BaseCommand):
    help = "Lance le moteur de simulation : fait avancer toutes les missions en cours en boucle."

    def add_arguments(self, parser):
        parser.add_argument(
            "--vitesse",
            type=float,
            default=60.0,
            help="Facteur d'acceleration (defaut 60 : 1 sec reelle = 60 sec simulees).",
        )
        parser.add_argument(
            "--intervalle",
            type=float,
            default=1.0,
            help="Delai en secondes entre 2 ticks (defaut 1.0).",
        )

    def handle(self, *args, **options):
        vitesse = options["vitesse"]
        intervalle = options["intervalle"]

        # Calcul des minutes simulees par tick
        minutes_par_tick = (intervalle * vitesse) / 60.0

        self.stdout.write(self.style.SUCCESS(
            f"=== Moteur de simulation demarre ==="
        ))
        self.stdout.write(f"  Vitesse        : x{vitesse:.0f}")
        self.stdout.write(f"  Intervalle tick: {intervalle:.1f} sec reelles")
        self.stdout.write(f"  Avancement     : {minutes_par_tick:.2f} min simulees / tick")
        self.stdout.write(self.style.WARNING("Appuie sur Ctrl+C pour arreter."))
        self.stdout.write("")

        # Gestion propre de Ctrl+C
        def handler(sig, frame):
            self.stdout.write("\n" + self.style.WARNING("Arret demande, fermeture..."))
            sys.exit(0)
        signal.signal(signal.SIGINT, handler)

        # Boucle principale
        compteur_ticks = 0
        while True:
            compteur_ticks += 1
            try:
                self.tick(minutes_par_tick, compteur_ticks)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Erreur dans tick #{compteur_ticks} : {e}"))
                # On continue malgre l'erreur pour ne pas planter le simulateur
            time.sleep(intervalle)

    def tick(self, minutes_par_tick, compteur):
        """Un tick : fait avancer toutes les missions en cours."""
        # On rafraichit le queryset a chaque tick pour prendre en compte
        # les nouvelles missions demarrees pendant que le simulateur tourne.
        missions = Mission.objects.filter(
            statut=Mission.Statut.EN_COURS
        ).select_related("camion", "chauffeur", "ville_depart", "ville_arrivee")

        if not missions.exists():
            # Toutes les 30 ticks, on signale qu'on est en attente
            if compteur % 30 == 0:
                self.stdout.write(f"[tick {compteur}] Aucune mission en cours, en attente...")
            return

        for mission in missions:
            try:
                resultat = avancer_mission(mission, minutes_par_tick)
                if resultat.get("ignored"):
                    continue

                progression = (resultat["distance_apres"] / float(mission.distance_totale_km or 1)) * 100
                msg = (
                    f"[tick {compteur}] {mission.reference} : "
                    f"{resultat['distance_apres']:.1f}/{mission.distance_totale_km} km "
                    f"({progression:.0f}%)"
                )
                if resultat["evenements"]:
                    msg += f" | +{resultat['evenements']} evenement(s)"

                if resultat["fini"]:
                    if resultat["succes"]:
                        self.stdout.write(self.style.SUCCESS(msg + " | TERMINEE OK"))
                    else:
                        self.stdout.write(self.style.ERROR(msg + " | ECHEC"))
                else:
                    self.stdout.write(msg)
            except Exception as e:
                self.stdout.write(self.style.ERROR(
                    f"[tick {compteur}] Erreur sur {mission.reference} : {e}"
                ))
