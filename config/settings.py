"""
Django settings for Behanian_Project project.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Charge le fichier .env s'il existe (développement local et VPS)
load_dotenv(BASE_DIR / '.env')

# ---------------------------------------------------------------------------
# SÉCURITÉ — lire depuis les variables d'environnement pour la production.
# En développement, créer un fichier .env à la racine et y définir ces valeurs.
# ---------------------------------------------------------------------------

SECRET_KEY = os.environ.get(
    'DJANGO_SECRET_KEY',
    'django-insecure-change-me-in-production'
)

DEBUG = os.environ.get('DJANGO_DEBUG', 'True') == 'True'

_allowed = os.environ.get('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1,testserver')
ALLOWED_HOSTS = [h.strip() for h in _allowed.split(',') if h.strip()]


# ---------------------------------------------------------------------------
# Application definition
# ---------------------------------------------------------------------------

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'widget_tweaks',

    # Apps du projet
    'users',
    'dashboard',
    'hotel',
    'restaurant',
    'bar',
    'piscine',
    'boite_nuit',
    'espaces_evenementiels',
    'cuisine',
    'rapport',
    'caisse',
    'facturation',
    'parametres',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',          # sert les fichiers statiques en production
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    # Middlewares maison — après AuthenticationMiddleware (besoin de request.user)
    'utils.middleware.StrictGroupAccessMiddleware',
    'caisse.middleware.CaisseOuverteMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'utils.context_processors.user_permissions_context',
            ],
            'builtins': [
                'dashboard.templatetags.montant_filter',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# ---------------------------------------------------------------------------
# Base de données
# Par défaut SQLite (développement). En production, remplacer par PostgreSQL
# via la variable d'environnement DATABASE_URL ou les variables individuelles.
# ---------------------------------------------------------------------------

DATABASES = {
    'default': {
        'ENGINE':   os.environ.get('DB_ENGINE',   'django.db.backends.sqlite3'),
        'NAME':     os.environ.get('DB_NAME',     str(BASE_DIR / 'db.sqlite3')),
        'USER':     os.environ.get('DB_USER',     ''),
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),
        'HOST':     os.environ.get('DB_HOST',     ''),
        'PORT':     os.environ.get('DB_PORT',     ''),
    }
}


# ---------------------------------------------------------------------------
# Password validation
# ---------------------------------------------------------------------------

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# ---------------------------------------------------------------------------
# Internationalisation
# ---------------------------------------------------------------------------

LANGUAGE_CODE = 'fr-fr'
TIME_ZONE     = 'GMT'
USE_I18N      = True
USE_TZ        = True


# ---------------------------------------------------------------------------
# Fichiers statiques
# ---------------------------------------------------------------------------

STATIC_URL       = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT      = BASE_DIR / 'staticfiles'

# Whitenoise : compression + hashes pour le cache navigateur en production
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'


# ---------------------------------------------------------------------------
# Fichiers media (uploads)
# ---------------------------------------------------------------------------

MEDIA_URL  = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'


# ---------------------------------------------------------------------------
# Email
# En développement : affiche les emails dans la console.
# En production : définir EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
#                 et les variables EMAIL_HOST, EMAIL_PORT, EMAIL_HOST_USER, etc.
# ---------------------------------------------------------------------------

EMAIL_BACKEND = os.environ.get(
    'EMAIL_BACKEND',
    'django.core.mail.backends.console.EmailBackend'
)
EMAIL_HOST         = os.environ.get('EMAIL_HOST', '')
EMAIL_PORT         = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_USE_TLS      = os.environ.get('EMAIL_USE_TLS', 'True') == 'True'
EMAIL_HOST_USER    = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')


# ---------------------------------------------------------------------------
# Sécurité HTTPS — activé automatiquement si DJANGO_DEBUG=False en production
# ---------------------------------------------------------------------------

if not DEBUG:
    SECURE_SSL_REDIRECT          = True
    SECURE_HSTS_SECONDS          = 31536000   # 1 an
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD          = True
    SESSION_COOKIE_SECURE        = True
    CSRF_COOKIE_SECURE           = True


# ---------------------------------------------------------------------------
# Clé primaire par défaut
# ---------------------------------------------------------------------------

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ---------------------------------------------------------------------------
# Authentification
# ---------------------------------------------------------------------------

LOGIN_URL             = 'login'
LOGIN_REDIRECT_URL    = 'dashboard:index'
LOGOUT_REDIRECT_URL   = 'login'


# ---------------------------------------------------------------------------
# CSRF — le JS doit pouvoir lire le token pour les appels AJAX
# ---------------------------------------------------------------------------

CSRF_COOKIE_HTTPONLY = False   # Le JS doit lire le cookie
CSRF_USE_SESSIONS    = False   # Token dans cookie (défaut Django, compatible AJAX)


# ---------------------------------------------------------------------------
# Session — expiration à la fermeture du navigateur
# ---------------------------------------------------------------------------

SESSION_EXPIRE_AT_BROWSER_CLOSE = True
