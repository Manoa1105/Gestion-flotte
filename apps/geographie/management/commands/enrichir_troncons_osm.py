"""
=============================================================================
Commande : enrichir_troncons_osm
=============================================================================
Telecharge via OSRM (OpenStreetMap Routing Machine) la polyline reelle
de chaque troncon de route, suivant les vraies routes physiques de Madagascar.

Sans cette commande, les trajets sont dessines en ligne droite entre les villes.
Avec, ils suivent les vraies routes nationales (RN2, RN4, RN7, etc.).

Lancement :
    python manage.py enrichir_troncons_osm           # tous les troncons sans polyline
    python manage.py enrichir_troncons_osm --reset   # force le re-telechargement
    python manage.py enrichir_troncons_osm --troncon 5  # un seul troncon

Service utilise : router.project-osrm.org (gratuit, rate limit raisonnable).
La commande attend ~1 sec entre chaque requete pour rester fair-play.

Pre-requis : connexion Internet active.
=============================================================================
"""

import os
import time
import json
from urllib.request import urlopen, Request
from urllib.error import URLError

from django.core.management.base import BaseCommand

from apps.geographie.models import TronconRoute


DELAI_ENTRE_REQUETES = 1.0


def _get_osrm_base():
    """Renvoie l'URL OSRM lue depuis OSRM_URL (.env), publique par defaut."""
    base = os.environ.get("OSRM_URL", "https://router.project-osrm.org").rstrip("/")
    return f"{base}/route/v1/driving"


def _est_local(url):
    """Detecte si l'URL pointe vers un serveur local (pas de rate-limit a respecter)."""
    return "localhost" in url or "127.0.0.1" in url or "osrm:" in url


def appeler_osrm(lon_depart, lat_depart, lon_arrivee, lat_arrivee, timeout=20):
    """
    Appelle OSRM et renvoie la geometrie GeoJSON LineString,
    ou None en cas d'echec.
    """
    url = (
        f"{_get_osrm_base()}/{lon_depart},{lat_depart};{lon_arrivee},{lat_arrivee}"
        f"?overview=full&geometries=geojson"
    )
    req = Request(url, headers={"User-Agent": "GestionFlotte-Madagascar/1.0"})
    try:
        with urlopen(req, timeout=timeout) as r:
            data = json.loads(r.read().decode("utf-8"))
    except URLError as e:
        return None, f"Erreur reseau : {e}"
    except json.JSONDecodeError as e:
        return None, f"Reponse invalide : {e}"

    if data.get("code") != "Ok" or not data.get("routes"):
        return None, f"OSRM a refuse : {data.get('code')} - {data.get('message', '')}"

    route = data["routes"][0]
    return route["geometry"], {
        "distance_m": route.get("distance"),
        "duration_s": route.get("duration"),
        "nb_points": len(route["geometry"].get("coordinates", [])),
    }


class Command(BaseCommand):
    help = "Telecharge via OSRM les vraies polylines des troncons de routes."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Re-telecharge meme si une polyline est deja stockee.",
        )
        parser.add_argument(
            "--troncon",
            type=int,
            default=None,
            help="ID d'un troncon specifique a (re)traiter.",
        )

    def handle(self, *args, **options):
        # Selection des troncons a traiter
        qs = TronconRoute.objects.select_related("route", "ville_depart", "ville_arrivee")

        if options.get("troncon"):
            qs = qs.filter(pk=options["troncon"])
        elif not options.get("reset"):
            qs = qs.filter(polyline_geojson__isnull=True)

        total = qs.count()
        if total == 0:
            self.stdout.write(self.style.SUCCESS(
                "Tous les troncons ont deja une polyline. "
                "Utilise --reset pour re-telecharger."
            ))
            return

        # Adapter le delai selon le type de serveur (local = pas de pause necessaire)
        url_base = _get_osrm_base()
        local = _est_local(url_base)
        delai = 0.0 if local else DELAI_ENTRE_REQUETES

        self.stdout.write(self.style.MIGRATE_HEADING(
            f"Telechargement OSRM pour {total} troncon(s)..."
        ))
        self.stdout.write(f"  Serveur OSRM : {url_base}")
        if local:
            self.stdout.write(self.style.SUCCESS("  Mode LOCAL : pas de pause entre les requetes.\n"))
        else:
            self.stdout.write(self.style.WARNING(
                f"  Mode PUBLIC : pause de {delai}s entre chaque appel (politesse).\n"
            ))

        nb_ok = 0
        nb_erreurs = 0

        for i, troncon in enumerate(qs, 1):
            label = (
                f"  [{i}/{total}] {troncon.route.numero} : "
                f"{troncon.ville_depart.nom} -> {troncon.ville_arrivee.nom}"
            )
            self.stdout.write(label, ending=" ")

            geom, info = appeler_osrm(
                lon_depart=float(troncon.ville_depart.longitude),
                lat_depart=float(troncon.ville_depart.latitude),
                lon_arrivee=float(troncon.ville_arrivee.longitude),
                lat_arrivee=float(troncon.ville_arrivee.latitude),
            )

            if geom is None:
                self.stdout.write(self.style.ERROR(f"ECHEC : {info}"))
                nb_erreurs += 1
            else:
                troncon.polyline_geojson = geom
                troncon.save(update_fields=["polyline_geojson"])
                self.stdout.write(self.style.SUCCESS(
                    f"OK ({info['nb_points']} points, {info['distance_m']/1000:.0f} km OSRM)"
                ))
                nb_ok += 1

            # Pause pour respecter le service public (zero si OSRM local)
            if i < total and delai > 0:
                time.sleep(delai)

        # Resume
        self.stdout.write(self.style.MIGRATE_HEADING("\n=== Resume ==="))
        self.stdout.write(f"  Reussis : {nb_ok}")
        self.stdout.write(f"  Echecs  : {nb_erreurs}")

        if nb_erreurs:
            self.stdout.write(self.style.WARNING(
                "\nLes troncons en echec garderont des lignes droites. "
                "Tu peux relancer la commande, OSRM reessaiera ceux qui n'ont pas de polyline."
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                "\nTous les troncons ont leur polyline reelle. "
                "Les missions afficheront maintenant les vraies routes."
            ))
