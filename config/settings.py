"""
=============================================================================
settings.py - Paramètres de configuration de Django
=============================================================================
Ce fichier centralise TOUS les paramètres du projet :
  - Quelles applications sont activées
  - Comment se connecter à la base de données
  - Où trouver les templates HTML et les fichiers statiques (CSS/JS)
  - La langue, le fuseau horaire, les règles de sécurité, etc.

Documentation officielle : https://docs.djangoproject.com/fr/5.0/topics/settings/
Liste complète des options : https://docs.djangoproject.com/fr/5.0/ref/settings/

Bonne pratique : on lit les valeurs sensibles (clé secrète, mot de passe BDD)
depuis le fichier .env, jamais en dur dans ce fichier.
=============================================================================
"""

from pathlib import Path
import os
from dotenv import load_dotenv


# -----------------------------------------------------------------------------
# CHARGEMENT DES VARIABLES D'ENVIRONNEMENT
# -----------------------------------------------------------------------------
# load_dotenv() lit le fichier .env à la racine du projet et rend ses variables
# disponibles via os.environ. Si le .env n'existe pas, ça ne plante pas.
load_dotenv()


# -----------------------------------------------------------------------------
# CHEMINS DU PROJET
# -----------------------------------------------------------------------------
# BASE_DIR = chemin absolu vers la racine du projet (le dossier qui contient manage.py)
BASE_DIR = Path(__file__).resolve().parent.parent


# -----------------------------------------------------------------------------
# SÉCURITÉ
# -----------------------------------------------------------------------------

# Clé secrète : utilisée pour signer cookies, sessions, tokens.
SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "django-insecure-cle-par-defaut-NE-PAS-UTILISER-EN-PRODUCTION",
)

# Mode debug : True = développement, False = production.
DEBUG = os.environ.get("DJANGO_DEBUG", "True") == "True"

# Liste des hôtes autorisés à servir l'app.
ALLOWED_HOSTS = os.environ.get(
    "DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1"
).split(",")


# -----------------------------------------------------------------------------
# APPLICATIONS INSTALLÉES
# -----------------------------------------------------------------------------
INSTALLED_APPS = [
    # Apps natives Django
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Nos apps personnalisées
    # L'ordre importe : geographie n'a aucune dépendance, on la met en premier.
    # flotte est indépendante. missions dépend des deux. simulation et finances
    # dépendent de missions. core agrège tout pour le dashboard.
    "apps.geographie",   # Régions, villes, routes nationales, tronçons
    "apps.flotte",       # Camions et chauffeurs
    "apps.missions",     # Missions de transport et positions GPS
    "apps.simulation",   # Types d'événements et événements survenus
    "apps.finances",     # Types de dépenses, dépenses, revenus
    "apps.comptes",      # Authentification et rôles utilisateurs
    "apps.core",         # Page d'accueil / tableau de bord
]


# -----------------------------------------------------------------------------
# MIDDLEWARES
# -----------------------------------------------------------------------------
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


# -----------------------------------------------------------------------------
# URLS PRINCIPALES
# -----------------------------------------------------------------------------
ROOT_URLCONF = "config.urls"


# -----------------------------------------------------------------------------
# TEMPLATES
# -----------------------------------------------------------------------------
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                # Injecte {{ profil_role }} dans tous les templates
                "apps.comptes.context_processors.role_courant",
            ],
        },
    },
]


# -----------------------------------------------------------------------------
# WSGI / ASGI
# -----------------------------------------------------------------------------
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"


# -----------------------------------------------------------------------------
# BASE DE DONNÉES
# -----------------------------------------------------------------------------
# On bascule entre SQLite (par défaut) et PostgreSQL via DATABASE_ENGINE.

DATABASE_ENGINE = os.environ.get("DATABASE_ENGINE", "sqlite").lower()

if DATABASE_ENGINE == "postgresql":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.environ.get("DATABASE_NAME", "gestion_flotte"),
            "USER": os.environ.get("DATABASE_USER", "postgres"),
            "PASSWORD": os.environ.get("DATABASE_PASSWORD", ""),
            "HOST": os.environ.get("DATABASE_HOST", "localhost"),
            "PORT": os.environ.get("DATABASE_PORT", "5432"),
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }


# -----------------------------------------------------------------------------
# VALIDATION DES MOTS DE PASSE
# -----------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# -----------------------------------------------------------------------------
# INTERNATIONALISATION ET LOCALISATION (Madagascar)
# -----------------------------------------------------------------------------
LANGUAGE_CODE = os.environ.get("LANGUAGE_CODE", "fr-fr")
TIME_ZONE = os.environ.get("TIME_ZONE", "Indian/Antananarivo")
USE_I18N = True
USE_TZ = True


# -----------------------------------------------------------------------------
# FICHIERS STATIQUES (CSS, JavaScript, images du site)
# -----------------------------------------------------------------------------
STATIC_URL = "/static/"
STATICFILES_DIRS = [
    BASE_DIR / "static",
]
STATIC_ROOT = BASE_DIR / "staticfiles"


# -----------------------------------------------------------------------------
# FICHIERS MEDIA (uploadés par les utilisateurs : photos de camions, etc.)
# -----------------------------------------------------------------------------
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"


# -----------------------------------------------------------------------------
# TYPE DE CHAMP AUTO-INCRÉMENT PAR DÉFAUT POUR LES CLÉS PRIMAIRES
# -----------------------------------------------------------------------------
# BigAutoField = entier 64 bits (jusqu'à ~9 quintillions). Recommandé.
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# -----------------------------------------------------------------------------
# AUTHENTIFICATION
# -----------------------------------------------------------------------------
# URL vers laquelle Django redirige quand @login_required est déclenché.
# Sans ça, Django cherche /accounts/login/ (la valeur par défaut).
LOGIN_URL = "/comptes/connexion/"

# Après connexion, si pas de paramètre ?next=, on va au tableau de bord.
LOGIN_REDIRECT_URL = "/"
