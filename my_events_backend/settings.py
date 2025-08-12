# my_events_backend/settings.py
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── Paths
BASE_DIR = Path(__file__).resolve().parent.parent

# ── Security / Core
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-do-not-use-in-prod")
DEBUG = True
ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

# ── Apps
INSTALLED_APPS = [
    # Django core
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # My apps
    "events",
    "users",
    "rest_framework"
    # "corsheaders",  # CORS για React (προαιρετικό)
]

# ── Middleware
MIDDLEWARE = [
    # "corsheaders.middleware.CorsMiddleware",  #  CORS
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# ── URL / WSGI
ROOT_URLCONF = "my_events_backend.urls"
WSGI_APPLICATION = "my_events_backend.wsgi.application"

# ── Templates
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
            ],
        },
    },
]

# ── Database 
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ── Internationalization
LANGUAGE_CODE = "el"
TIME_ZONE = "Europe/Athens"
USE_I18N = True
USE_TZ = True

# ── Static
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"] if (BASE_DIR / "static").exists() else []

# ── Auth (custom User)
AUTH_USER_MODEL = "users.User"

# ── CORS 
# CORS_ALLOWED_ORIGINS = [
#     "http://localhost:3000",
#     "http://localhost:5173",
# ]

# ── Mongo (Atlas) – my_events_backend/mongo.py
MONGODB_URI = os.getenv("MONGODB_URI")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "my_events_backend")
MONGODB_EVENTS_COLLECTION = os.getenv("MONGODB_EVENTS_COLLECTION", "events")
MONGODB_USERS_COLLECTION = os.getenv("MONGODB_USERS_COLLECTION", "users")
