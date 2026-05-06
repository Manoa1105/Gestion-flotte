# OSRM Local pour Madagascar

Serveur de calcul d'itinéraires basé sur **OpenStreetMap**, hébergé en
local via Docker. Permet de calculer des trajets sur **toutes les routes
de Madagascar** (RN, RIP, pistes), sans dépendre du service public OSRM
ni de ses limites de débit.

## Pré-requis

- **Docker Desktop** installé et en cours d'exécution
  → https://www.docker.com/products/docker-desktop/
- ~500 Mo d'espace disque libre
- Connexion Internet (pour le téléchargement initial)

Vérifie ton installation :

```powershell
docker --version
docker compose version
```

## Installation (5 minutes, à faire une seule fois)

### 1. Télécharger l'extract OSM Madagascar

Va sur **https://download.geofabrik.de/africa/madagascar.html**

Télécharge `madagascar-latest.osm.pbf` (~50 Mo) et place-le dans le dossier
**`docker/osrm/data/`** du projet :

```
Gestion_flotte/
└── docker/
    └── osrm/
        ├── docker-compose.yml
        └── data/
            └── madagascar-latest.osm.pbf   ← ICI
```

### 2. Pré-traiter les données OSM

Dans PowerShell, depuis le dossier `docker/osrm/` :

```powershell
cd docker\osrm
docker compose --profile prepare run --rm osrm-prepare
```

Tu vas voir défiler :

```
[1/3] Extraction du graphe routier (peut durer 1-3 min)...
[2/3] Partitionnement (Multi-Level Dijkstra)...
[3/3] Customization...
Pré-traitement terminé.
```

Cette étape génère ~200 Mo de fichiers `madagascar-latest.osrm.*` dans `data/`.

### 3. Lancer le serveur OSRM

```powershell
docker compose up -d osrm
```

Le serveur tourne maintenant en arrière-plan sur **http://localhost:5000**.

Vérifier qu'il répond :

```powershell
# Test : route Antananarivo → Toamasina
curl "http://localhost:5000/route/v1/driving/47.5079,-18.8792;49.4023,-18.1492?overview=false"
```

Tu dois recevoir un JSON avec `"code":"Ok"` et la distance/durée.

### 4. Configurer le projet pour utiliser OSRM local

Dans ton fichier `.env` à la racine du projet, change la ligne `OSRM_URL` :

```
OSRM_URL=http://localhost:5000
```

(au lieu de `https://router.project-osrm.org`)

### 5. Re-télécharger les polylines avec ton OSRM local

```powershell
cd ..\..\
python manage.py enrichir_troncons_osm --reset
```

Tu vas voir :

```
Serveur OSRM : http://localhost:5000/route/v1/driving
Mode LOCAL : pas de pause entre les requêtes.

[1/23] RN2 : Antananarivo -> Moramanga       OK (412 points, 110 km)
[2/23] RN2 : Moramanga -> Toamasina          OK (1247 points, 263 km)
...
```

Le `--reset` force le re-téléchargement de toutes les polylines (qui seront
plus précises avec ton serveur local). En mode local, **pas de pause** entre
les requêtes : 23 tronçons traités en quelques secondes au lieu de 25 secondes.

## Commandes utiles au quotidien

```powershell
# Voir si OSRM tourne
docker compose ps

# Logs en direct
docker compose logs -f osrm

# Arrêter le serveur (libère le port 5000)
docker compose stop osrm

# Redémarrer
docker compose start osrm

# Tout arrêter et supprimer les containers
docker compose down

# Mettre à jour avec une version récente d'OSM
# (à faire ~2 fois par an)
# 1. Télécharge la nouvelle version depuis Geofabrik
# 2. Supprime les anciens fichiers .osrm.* dans data/
# 3. Re-lance les étapes 2 et 3
```

## Avantages vs OSRM public

| | Public | Local |
|---|---|---|
| Latence | 500-1000 ms | < 50 ms |
| Rate-limit | ~100 requêtes/min | Illimité |
| Disponibilité | Dépend du service | 100% |
| Coût | Gratuit | Gratuit |
| Espace disque | 0 | ~500 Mo |
| Internet requis | Oui | Non (après setup) |

## Dépannage

**Erreur "port 5000 déjà utilisé"** : un autre service occupe le port.
Modifie `docker-compose.yml` : remplace `"5000:5000"` par `"5001:5000"` et
mets `OSRM_URL=http://localhost:5001` dans `.env`.

**Erreur "no such file: madagascar-latest.osm.pbf"** : tu as oublié l'étape 1,
le fichier doit être dans `docker/osrm/data/`.

**Le pré-traitement plante** : vérifie que tu as au moins 2 Go de RAM libre
pour Docker Desktop (Settings > Resources).

**OSRM répond mais pas de polyline** : vérifie que `osrm-routed` tourne avec
l'option `--algorithm mld` (c'est le cas dans le docker-compose fourni).

## Aller plus loin

Pour des données encore plus à jour, tu peux utiliser un **profil de routage
spécifique camion** au lieu du profil voiture par défaut. OSRM fournit
`truck.lua` qui prend en compte les restrictions poids lourds. Modifie le
`command` du service `osrm-prepare` dans `docker-compose.yml` :

```yaml
osrm-extract -p /opt/truck.lua /data/madagascar-latest.osm.pbf
```

(par défaut on utilise `car.lua` qui suffit pour Madagascar où les
restrictions poids lourds sont rares).
