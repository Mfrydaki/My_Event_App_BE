import os
from pathlib import Path
from dotenv import load_dotenv
from corsheaders.defaults import default_headers

# Paths & .env
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env (placed next to manage.py)
load_dotenv(str(BASE_DIR / ".env"))

# Core Django settings
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-do-not-use-in-prod")
DEBUG = os.getenv("DEBUG", "True") == "True"

# Add your frontend dev hosts here
ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

# Installed apps: keep Django core, DRF, CORS, and your project apps
INSTALLED_APPS = [
    # Django core
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Third-party
    "rest_framework",
    "corsheaders",

    # Project apps (PyMongo-based code — no Django ORM models required)
    "events",
    "users",
]

# TEMPLATES (keep default configuration)
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],  # Optional: put HTML templates here
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# Middleware: CORS must come before CommonMiddleware
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "my_events_backend.urls"
WSGI_APPLICATION = "my_events_backend.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# Internationalization / Timezone
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Europe/Athens"
USE_I18N = True
USE_TZ = True

# Static files (DEV/PROD)
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"] if (BASE_DIR / "static").exists() else []

# CORS / CSRF (for React dev servers on 3000/5173)
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
CORS_ALLOW_HEADERS = list(default_headers) + ["authorization"]

CSRF_TRUSTED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

# DRF minimal config (JSON responses by default)
REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
    ],
}

# MongoDB / JWT from .env (used by your PyMongo code)
MONGODB_URI = os.getenv("MONGODB_URI")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "my_events_db")
MONGODB_EVENTS_COLLECTION = os.getenv("MONGODB_EVENTS_COLLECTION", "events")
MONGODB_USERS_COLLECTION = os.getenv("MONGODB_USERS_COLLECTION", "users")

JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ACCESS_MINUTES = int(os.getenv("JWT_ACCESS_MINUTES", 60))

# Logging (helpful during development)
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {"class": "logging.StreamHandler"},
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO" if DEBUG else "WARNING",
    },
}

# On startup, print a small sanity line (DEV only)
if DEBUG:
    # Avoid printing the full URI for security; just show whether it's loaded.
    print("✅ settings.py loaded | .env MONGODB_URI present:", bool(MONGODB_URI))
