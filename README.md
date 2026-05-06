# Gestion de Flotte — Camions Semi-Remorques (Madagascar)

Application web de gestion d'une flotte de camions semi-remorques avec
**simulateur de missions hyper réaliste**, pensée pour le contexte
malgache (routes nationales, villes, conditions locales).

Au-delà de la gestion classique, l'application intègre dès le départ un
moteur de simulation type "jeu vidéo" : on ajoute un camion, on lui assigne
une mission, on valide, et le camion exécute son trajet en temps accéléré
en générant des événements réalistes (pannes, embouteillages, contrôles,
conditions météo, etc.). L'objectif à terme est de connecter le système
à de vrais capteurs IoT et d'exploiter les données générées en Big Data.

---

## Stack technique

- **Backend** : Python 3.10+ / Django 5
- **Frontend** : HTMX (interactions dynamiques) + Tailwind CSS
- **Base de données** : SQLite en développement, PostgreSQL en production
- **Cartographie** : Leaflet + OpenStreetMap
- **Tâches asynchrones** (à venir) : Celery + Redis pour le moteur de simulation
- **Temps réel** (à venir) : Django Channels (WebSockets) pour le suivi live des camions

---

## Pré-requis

- Python 3.10 ou supérieur
- pip (inclus avec Python)
- Node.js 18 ou supérieur (pour la compilation Tailwind CSS)
- npm (inclus avec Node.js)
- Git (pour le versionnement)

Vérifier que tout est bien installé :

```bash
python --version
node --version
npm --version
```

Si Node.js est manquant, télécharge la version LTS depuis https://nodejs.org/.

---

## Installation (premier démarrage)

### 1. Récupérer le projet

```bash
git clone <url-du-depot> Gestion_flotte
cd Gestion_flotte
```

### 2. Créer et activer un environnement virtuel

Un environnement virtuel (venv) isole les bibliothèques du projet du
système Python global. Indispensable.

**Sous Windows (PowerShell)** :

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**Sous Windows (CMD)** :

```cmd
python -m venv .venv
.venv\Scripts\activate.bat
```

**Sous macOS / Linux** :

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Après activation, le préfixe `(.venv)` apparaît au début de ta ligne de commande.

### 3. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 4. Créer le fichier `.env`

Le fichier `.env` contient les variables sensibles (clé secrète, mot de passe BDD).
Il n'est jamais versionné. On le crée à partir du modèle fourni :

**Sous Windows (PowerShell)** :

```powershell
Copy-Item .env.example .env
```

**Sous Windows (CMD)** :

```cmd
copy .env.example .env
```

**Sous macOS / Linux** :

```bash
cp .env.example .env
```

Ensuite, ouvre le fichier `.env` et remplace `DJANGO_SECRET_KEY` par une vraie
clé aléatoire. Tu peux en générer une avec :

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 5. Créer la base de données

Cette commande crée le fichier `db.sqlite3` et applique les tables nécessaires
à Django (utilisateurs, sessions, etc.) :

```bash
python manage.py migrate
```

### 6. Créer un compte administrateur

```bash
python manage.py createsuperuser
```

Entre un nom d'utilisateur, un email (optionnel) et un mot de passe.

### 7. Installer les dépendances frontend (Tailwind CSS)

```bash
npm install
```

Cette commande installe Tailwind dans un dossier `node_modules/` (gitignored).

### 8. Compiler le CSS

Le fichier `static/css/dist/output.css` est généré à partir de `static/css/input.css`
et des classes Tailwind utilisées dans les templates HTML.

Pour le compiler une fois :

```bash
npm run build-css
```

Pour le compiler en mode "watch" (recompilation automatique à chaque modification
de fichier HTML ou CSS — à laisser tourner pendant le développement) :

```bash
npm run watch-css
```

### 9. Lancer le serveur de développement

Dans un **autre terminal** (laisse `npm run watch-css` tourner dans le premier) :

```bash
python manage.py runserver
```

L'application est maintenant accessible sur **http://localhost:8000**.
L'interface d'administration est sur **http://localhost:8000/admin/**.

> **Astuce :** pendant le développement, ouvre deux terminaux côte à côte :
> - Terminal 1 : `npm run watch-css` (recompile Tailwind à chaque changement)
> - Terminal 2 : `python manage.py runserver` (sert l'application)

---

## Structure du projet

```
Gestion_flotte/
├── .env.example          Modèle des variables d'environnement
├── .gitignore            Fichiers à ne pas versionner
├── README.md             Ce fichier
├── requirements.txt      Liste des bibliothèques Python
├── manage.py             Script de gestion Django (commandes)
│
├── config/               Configuration centrale du projet Django
│   ├── settings.py       Tous les paramètres
│   ├── urls.py           Routage principal
│   ├── wsgi.py           Point d'entrée production (synchrone)
│   └── asgi.py           Point d'entrée production (asynchrone)
│
├── apps/                 Toutes les applications Django du projet
│   └── (à venir : flotte, missions, simulation, finances, geographie)
│
├── static/               Fichiers statiques globaux (CSS, JS, images)
├── templates/            Templates HTML globaux (base.html, etc.)
└── media/                Fichiers uploadés par les utilisateurs (gitignored)
```

---

## Commandes utiles au quotidien

```bash
# Lancer le serveur de développement
python manage.py runserver

# Créer une nouvelle app (à exécuter depuis le dossier apps/)
cd apps && python ../manage.py startapp NOM_DE_L_APP

# Après avoir modifié un modèle :
python manage.py makemigrations    # Crée le fichier de migration
python manage.py migrate           # Applique la migration à la BDD

# Ouvrir un shell Python avec Django chargé (pour tester du code)
python manage.py shell

# Lister toutes les commandes Django disponibles
python manage.py help
```

---

## Feuille de route

L'application est construite par étapes successives :

1. ✅ Mise en place de l'environnement et structure du projet
2. ⬜ Modélisation des données (camions, chauffeurs, missions, finances...)
3. ⬜ Interface d'administration Django
4. ⬜ Pré-remplissage de la géographie de Madagascar (villes, routes nationales)
5. ⬜ Création et validation de missions (sans simulation encore)
6. ⬜ Moteur de simulation avec Celery (les camions avancent en arrière-plan)
7. ⬜ Système d'événements aléatoires durant les missions
8. ⬜ Carte Leaflet temps réel (positions des camions)
9. ⬜ Module de gestion budgétaire et rentabilité
10. ⬜ Tableau de bord global

---

## Licence

Projet personnel d'apprentissage. Tous droits réservés.
