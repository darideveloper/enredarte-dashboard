import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from django.templatetags.static import static
BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")
ENV = os.getenv("ENV", "dev")

load_dotenv(BASE_DIR / f".env.{ENV}")

SECRET_KEY = os.getenv("SECRET_KEY")

DEBUG = os.getenv("DEBUG", "False") == "True"

ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "").split(",")

INSTALLED_APPS = [
    "unfold",
    "unfold.contrib.filters",
    "unfold.contrib.forms",
    "unfold.contrib.inlines",
    "corsheaders",
    "rest_framework",
    "rest_framework.authtoken",
    "django_filters",
    "solo",
    "storages",
    "artworks",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "project.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "project" / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "utils.context_processors.user_palette",
            ],
            "libraries": {
                "sidebar_extras": "utils.templatetags.sidebar_extras",
            },
        },
    },
]

WSGI_APPLICATION = "project.wsgi.application"

IS_TESTING = len(sys.argv) > 1 and sys.argv[1] == "test"

if IS_TESTING:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "testing.sqlite3",
        }
    }
else:
    options = {}
    if os.environ.get("DB_ENGINE") == "django.db.backends.mysql":
        options = {
            "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
            "charset": "utf8mb4",
        }

    DATABASES = {
        "default": {
            "ENGINE": os.environ.get("DB_ENGINE", "django.db.backends.sqlite3"),
            "NAME": os.environ.get("DB_NAME", BASE_DIR / "db.sqlite3"),
            "USER": os.environ.get("DB_USER", ""),
            "PASSWORD": os.environ.get("DB_PASSWORD", ""),
            "HOST": os.environ.get("DB_HOST", "localhost"),
            "PORT": os.environ.get("DB_PORT", ""),
            "OPTIONS": options,
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "es"
TIME_ZONE = "America/Mexico_City"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
MEDIA_URL = "/media/"

STATICFILES_DIRS = [
    BASE_DIR / "static",
]
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

cors_allowed = os.getenv("CORS_ALLOWED_ORIGINS")
if cors_allowed and cors_allowed != "None":
    CORS_ALLOWED_ORIGINS = [
        origin.strip().rstrip("/") for origin in cors_allowed.split(",") if origin.strip()
    ]

csrf_trusted = os.getenv("CSRF_TRUSTED_ORIGINS")
if csrf_trusted and csrf_trusted != "None":
    CSRF_TRUSTED_ORIGINS = [
        origin.strip().rstrip("/") for origin in csrf_trusted.split(",") if origin.strip()
    ]

DATE_FORMAT = "d/b/Y"
TIME_FORMAT = "H:i"
DATETIME_FORMAT = f"{DATE_FORMAT} {TIME_FORMAT}"

# Storage
STORAGE_AWS = os.getenv("STORAGE_AWS") == "True"

if STORAGE_AWS:
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_STORAGE_BUCKET_NAME = os.getenv("AWS_STORAGE_BUCKET_NAME")
    AWS_S3_REGION_NAME = os.getenv("AWS_S3_REGION_NAME")
    AWS_S3_ENDPOINT_URL = os.getenv("AWS_S3_ENDPOINT_URL")
    AWS_S3_CUSTOM_DOMAIN = os.getenv("AWS_S3_CUSTOM_DOMAIN")
    AWS_PROJECT_FOLDER = os.getenv("AWS_PROJECT_FOLDER")

    STATIC_LOCATION = f"{AWS_PROJECT_FOLDER}/static"
    PUBLIC_MEDIA_LOCATION = f"{AWS_PROJECT_FOLDER}/media"
    PRIVATE_MEDIA_LOCATION = f"{AWS_PROJECT_FOLDER}/private"

    AWS_S3_OBJECT_PARAMETERS = {"CacheControl": "max-age=86400"}
    AWS_DEFAULT_ACL = None

    STORAGES = {
        "default": {
            "BACKEND": "project.storage_backends.PublicMediaStorage",
        },
        "staticfiles": {
            "BACKEND": "project.storage_backends.StaticStorage",
        },
        "private": {
            "BACKEND": "project.storage_backends.PrivateMediaStorage",
        },
    }
else:
    STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
        },
    }

# DRF
REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_PAGINATION_CLASS": "project.pagination.CustomPageNumberPagination",
    "PAGE_SIZE": 12,
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework.authentication.TokenAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ),
    "EXCEPTION_HANDLER": "project.handlers.custom_exception_handler",
}

# Unfold
UNFOLD = {
    "SITE_TITLE": "Enredarte Admin",
    "SITE_HEADER": "ENREDARTE DASHBOARD",
    "SITE_SUBHEADER": "Sistema de gestión",
    "SITE_URL": "/",
    "SITE_ICON": lambda request: static("favicon.png"),
    "SITE_SYMBOL": "palette",
    "SITE_FAVICONS": [
        {
            "rel": "icon",
            "sizes": "32x32",
            "type": "image/png",
            "href": lambda request: static("favicon.png"),
        },
    ],
    "SHOW_HISTORY": True,
    "SHOW_VIEW_ON_SITE": True,
    "ENVIRONMENT": "utils.callbacks.environment_callback",
    "THEME": "light",
    "COLORS": {
        "primary": {
            "50": "oklch(0.97 0.02 20)",
            "100": "oklch(0.92 0.04 20)",
            "200": "oklch(0.85 0.08 20)",
            "300": "oklch(0.75 0.12 20)",
            "400": "oklch(0.64 0.17 20)",
            "500": "oklch(0.53 0.20 20)",
            "600": "oklch(0.44 0.18 20)",
            "700": "oklch(0.36 0.15 20)",
            "800": "oklch(0.29 0.12 20)",
            "900": "oklch(0.22 0.08 20)",
            "950": "oklch(0.17 0.04 20)",
        },
    },
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": True,
        "navigation": [],
    },
}
