---
created: 2026-04-18
updated: 2026-04-18
tags:
  - django
  - setup
  - documentation
type: resource
status: active
---

# Project Setup Guide

Follow these steps to set up the `enredarte-dashboard` project from scratch.

### 1. Add requirements.txt
Create a `requirements.txt` file in the root directory with the following dependencies:

```text
# base
Django>=5.2,<5.3           # Core web framework
whitenoise>=6.11.0          # Static file serving for production
gunicorn>=24.1.1           # Production WSGI server
django-cors-headers>=4.9.0 # CORS handling for API access
python-dotenv>=1.0.1      # Environment variable management

# db
psycopg>=3.2.3             # PostgreSQL database adapter

# images
pillow>=11.1.0             # Image processing library

# drf & jwt
djangorestframework>=3.16.1 # REST API toolkit
django-filter>=24.3        # Dynamic API filtering

# payments
stripe>=15.5.1,<16         # Stripe SDK for artist subscriptions

# testing
selenium>=4.40.0           # Browser automation for E2E tests

# admin
django-unfold==0.77.1      # Modern Django admin theme
django-solo>=2.3.0         # Singleton models for configuration

# tools
requests>=2.32.3           # HTTP library for external API calls

# storage
django-storages==1.14.4    # Custom storage backends (S3, etc.)
boto3==1.34.162            # AWS SDK for Python
```

### 2. Initial Commands
Run the following commands to initialize the environment and install dependencies:

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment (Linux/macOS)
source venv/bin/activate

# Activate virtual environment (Windows)
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start Django project
django-admin startproject project .
```

### 3. Create Initial App
Once the project is initialized, create the main application. 

> **Important:** The `{app_name}` should **ALWAYS** be prompted/requested from the user before executing this command.

```bash
python manage.py startapp {app_name}
```

> **Models:** every model created in this project (or replicated later) must
> follow the [[django-model-definitions|Model Definitions]] convention:
> `Meta.verbose_name`/`verbose_name_plural`, `verbose_name` on every field,
> `help_text` when needed, and a content-based `__str__`.

### 4. Git Initialization
Initialize a Git repository to track your changes and commit the initial project state.

```bash
# Initialize git
git init

# Create .gitignore file (abridged — see repo .gitignore for the full version,
# which also covers venv, .env* (except *.example), bruno environments,
# sqlite, staticfiles/media, IDE files, credentials.json, and .*/ dotfiles)
cat <<EOF > .gitignore
__pycache__
*__pycache__
*temp.*
temp.*
*.log*
*.zip
venv
.env
debug.*
db.*
*.sqlite3
*.pyc
credentials.json
staticfiles/
info.txt
/media
.env*
.vscode
*/.DS_Store 
.DS_Store
/docs 
*.temp
.windsurf/
EOF

# Add all files and commit
git add .
git commit -m "initial project"
```

### 5. Environment Infrastructure
Establish the foundation for environment-variable-first configuration by creating the following files in the project root.

The `.env` file is a **pure selector**: it contains ONLY the `ENV` variable. All other configuration (secrets, debug, hosts, DB, storage, email, AWS) lives in `.env.dev` and `.env.prod` and is duplicated per environment as required.

> **Note:** If the project does not require email functionality, you can skip the `EMAIL_*` variables in the `.env.dev` and `.env.prod` files.
> **Note:** The `SECRET_KEY` should be a randomly generated string of at least 30 characters. Define it in BOTH `.env.dev` and `.env.prod` (the prod value is a placeholder that gets filled at deploy time).

**`.env`** (Environment selector — only this)
```env
ENV=dev
```

**`.env.dev`** (Local development defaults — mirrors `.env.dev.example`)
```env
SECRET_KEY=django-insecure-change-me-in-production
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,enredarte.localhost,enredarte-dashboard.localhost,enredarte-dashboard.<your-domain>
CORS_ALLOWED_ORIGINS=https://enredarte.localhost,https://enredarte-dashboard.localhost,https://enredarte-dashboard.<your-domain>
CSRF_TRUSTED_ORIGINS=https://enredarte.localhost,https://enredarte-dashboard.localhost,https://enredarte-dashboard.<your-domain>
HOST=http://enredarte-dashboard.localhost
DB_ENGINE=django.db.backends.postgresql
DB_NAME=enredarte
DB_USER=db_user
DB_PASSWORD=db_password
DB_HOST=localhost
DB_PORT=5432
STORAGE_AWS=False
STRIPE_SECRET_KEY=sk_test_xxxx
STRIPE_PUBLISHABLE_KEY=pk_test_xxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxx
STRIPE_API_VERSION=2026-07-29.dahlia
STRIPE_PRICE_ID=price_xxxx
DEPLOY_WEBHOOK_URL=https://apps.darideveloper.com/api/v1/deploy?uuid=XXXX&force=false
COOLIFY_API_TOKEN=xxxx
CLOUDFLARE_TUNNEL_NAME=enredarte-dashboard-dev
CLOUDFLARE_TUNNEL_HOST=enredarte-dashboard.<your-domain>

```

**`.env.prod`** (Production-ready placeholders — mirrors `.env.prod.example`)
```env
SECRET_KEY=django-insecure-change-me-in-production
DEBUG=False
ALLOWED_HOSTS=example.com,www.example.com
CORS_ALLOWED_ORIGINS=https://example.com
CSRF_TRUSTED_ORIGINS=https://example.com
HOST=https://example.com
DB_ENGINE=django.db.backends.postgresql
DB_NAME=your_db_name
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=your-db-host.amazonaws.com
DB_PORT=5432
STORAGE_AWS=True
AWS_ACCESS_KEY_ID=your-access-key-id
AWS_SECRET_ACCESS_KEY=your-secret-access-key
AWS_STORAGE_BUCKET_NAME=your-bucket-name
AWS_PROJECT_FOLDER=your-project-folder
AWS_S3_REGION_NAME=us-east-1
AWS_S3_ENDPOINT_URL=https://s3.amazonaws.com
AWS_S3_CUSTOM_DOMAIN=cdn.example.com
STRIPE_SECRET_KEY=sk_live_xxxx
STRIPE_PUBLISHABLE_KEY=pk_live_xxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxx
STRIPE_API_VERSION=2026-07-29.dahlia
STRIPE_PRICE_ID=price_xxxx
DEPLOY_WEBHOOK_URL=https://apps.darideveloper.com/api/v1/deploy?uuid=XXXX&force=false
COOLIFY_API_TOKEN=xxxx

```

### 6. Core Settings & App Integration
Refactor `project/settings.py` to initialize `python-dotenv`, load environment files, and register apps/middleware.

**Initialize Dotenv at the top of `settings.py`:**
```python
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env first to get ENV value
load_dotenv(BASE_DIR / '.env')
ENV = os.getenv('ENV', 'dev')

# Load environment-specific file (override=True so project config wins over shell-injected vars)
load_dotenv(BASE_DIR / f'.env.{ENV}', override=True)

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv("DEBUG", "False") == "True"

ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "").split(",")
```

**Update `INSTALLED_APPS` and `MIDDLEWARE`:**
- Include `unfold`, `unfold.contrib.filters`, `unfold.contrib.forms`, `unfold.contrib.inlines`, `corsheaders`, `rest_framework`, `rest_framework.authtoken`, `django_filters`, `solo`, and `storages`.
- **Add your local applications:** `core`, `artworks`, `blog`, `subscriptions` (plus the `{app_name}` you created in Step 3).
- Add `CorsMiddleware` and `WhiteNoiseMiddleware` to `MIDDLEWARE`.
- **Admin Theme:** The project uses [[django-unfold-admin|Django Unfold]] for a modern admin interface.

### 7. Database & Storage Strategy
Implement dynamic logic in `settings.py` to switch backends based on the environment. Detailed cloud storage configuration is available in [[django-media-storage]].

**Dynamic Database Selection:**
```python
import sys
IS_TESTING = len(sys.argv) > 1 and sys.argv[1] == "test"

if IS_TESTING:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": os.path.join(BASE_DIR, "testing.sqlite3"),
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
            "NAME": os.environ.get("DB_NAME", os.path.join(BASE_DIR, "db.sqlite3")),
            "USER": os.environ.get("DB_USER", ""),
            "PASSWORD": os.environ.get("DB_PASSWORD", ""),
            "HOST": os.environ.get("DB_HOST", "localhost"),
            "PORT": os.environ.get("DB_PORT", ""),
            "OPTIONS": options,
        }
    }
```

**Internationalization:**
> **Note:** This project runs a Spanish admin (`LANGUAGE_CODE = "es"`, `TIME_ZONE = "America/Mexico_City"`). See [[django-i18n-es-admin|Spanish Django Admin]].

```python
LANGUAGE_CODE = 'es'
TIME_ZONE = "America/Mexico_City"
USE_I18N = True
USE_TZ = True
```

**Static & Media Management:**
```python
STATIC_URL = 'static/'
MEDIA_URL = "/media/"

STATICFILES_DIRS = [
    BASE_DIR / "static",
]
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
MEDIA_ROOT = os.path.join(BASE_DIR, "media")
```

**Conditional Storage (AWS S3 vs Local):**
> Full storage configuration details are available in the
> [[django-media-storage|Media Storage Configuration]] guide.
```python
STORAGE_AWS = os.getenv("STORAGE_AWS") == "True"

if STORAGE_AWS:
    # AWS S3 Configuration
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_STORAGE_BUCKET_NAME = os.getenv("AWS_STORAGE_BUCKET_NAME")
    AWS_S3_REGION_NAME = os.getenv("AWS_S3_REGION_NAME")
    AWS_S3_ENDPOINT_URL = os.getenv("AWS_S3_ENDPOINT_URL")
    AWS_PROJECT_FOLDER = os.getenv("AWS_PROJECT_FOLDER")

    # Folder isolation inside the shared bucket
    STATIC_LOCATION = f"{AWS_PROJECT_FOLDER}/static"
    PUBLIC_MEDIA_LOCATION = f"{AWS_PROJECT_FOLDER}/media"
    PRIVATE_MEDIA_LOCATION = f"{AWS_PROJECT_FOLDER}/private"

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
    # Local Storage Configuration (no `private` key locally; S3 mode adds it).
    # During tests (`IS_TESTING`) the staticfiles backend falls back to
    # `StaticFilesStorage` so admin views render without a manifest.
    staticfiles_backend = (
        "django.contrib.staticfiles.storage.StaticFilesStorage"
        if IS_TESTING
        else "whitenoise.storage.CompressedManifestStaticFilesStorage"
    )
    STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
        "staticfiles": {
            "BACKEND": staticfiles_backend,
        },
    }
```

### 8. Security, API & Email Configuration
Finalize the configuration with security headers, DRF defaults, and SMTP settings.

> **Note:** Prompt the user to confirm if the project needs to send emails. If emails are not required, skip the **Email SMTP Configuration** subsection below and the corresponding environment variables in Step 5.

**CORS & CSRF Configuration:**
```python
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
```

**Django REST Framework Setup:**
```python
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
```

**Global DateTime Formatting:**

```python
DATE_FORMAT = "d/b/Y"
TIME_FORMAT = "H:i"
DATETIME_FORMAT = f"{DATE_FORMAT} {TIME_FORMAT}"
```

**Email SMTP Configuration:**
> **Note:** This project currently sends no email — no `EMAIL_*` settings exist in `settings.py`. Skip this subsection unless the project gains email functionality. If emails are required, add the block below and the corresponding variables per environment.

```python
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.getenv("EMAIL_HOST")
EMAIL_PORT = os.getenv("EMAIL_PORT")
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")
EMAIL_USE_SSL = os.getenv("EMAIL_USE_SSL") == "True"
EMAIL_FROM = EMAIL_HOST_USER
EMAILS_NOTIFICATIONS = os.getenv("EMAILS_NOTIFICATIONS", "").split(",")
```

### 9. Validation
Verify the project configuration and ensure that the test environment is correctly isolated.

```bash
# Verify the complete configuration
python manage.py check

# Run tests to ensure test-specific database isolation (canonical; do not use pytest)
python manage.py test
# or: venv/bin/python manage.py test --verbosity=2
```

> Canonical runner is `venv/bin/python manage.py test` (`python manage.py test` when venv active) per `openspec/specs/testing-contract/spec.md`; `pytest` is not supported.

### 10. Required Project Wiring
These files are essential for the infrastructure and global behaviors defined in `settings.py`.

#### project/urls.py
Global URL configuration with everything under `/api/`: `api/artworks/` (artworks app, authenticated), `api/blog/` (blog app, public posts), `admin/system/` (core publish flow), `subscriptions/` (success/cancel/portal-return pages), `webhooks/stripe/` (Stripe endpoint), plus admin and root redirect.
```python
import project.admin  # required: `project` is not in INSTALLED_APPS, so Django does not auto-discover its admin module; without this import the custom UserAdmin/GroupAdmin/TokenAdmin are silently ignored

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

from subscriptions import webhooks

urlpatterns = [
    # Admin Interface
    path("admin/", admin.site.urls),

    # Root Redirect to Admin
    path("", RedirectView.as_view(url="/admin/"), name="home-redirect-admin"),

    # API + app endpoints (all under /api/)
    path("admin/system/", include("core.urls")),
    path("api/artworks/", include("artworks.urls")),
    path("api/blog/", include("blog.urls")),
    path("subscriptions/", include(("subscriptions.urls", "subscriptions"), namespace="subscriptions")),
    path("webhooks/stripe/", webhooks.stripe_webhook),
]

# Serve Media Files in Development
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

#### project/pagination.py
Custom pagination logic for metadata-rich API responses.
```python
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

class CustomPageNumberPagination(PageNumberPagination):
    page_size = 12
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'page': self.page.number,
            'page_size': self.get_page_size(self.request),
            'total_pages': self.page.paginator.num_pages,
            'results': data
        })
```

#### project/storage_backends.py
Defines custom storage backends for S3 integration.
```python
from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage

class StaticStorage(S3Boto3Storage):
    """Handles static files (CSS, JS, images)."""
    location = settings.STATIC_LOCATION
    default_acl = "public-read"

class PublicMediaStorage(S3Boto3Storage):
    """Handles public uploads."""
    location = settings.PUBLIC_MEDIA_LOCATION
    default_acl = "public-read"
    file_overwrite = False

class PrivateMediaStorage(S3Boto3Storage):
    """Handles sensitive files."""
    location = settings.PRIVATE_MEDIA_LOCATION
    default_acl = "private"
    file_overwrite = False
    custom_domain = False
```

#### project/handlers.py
Custom exception handler for standardized API error responses.
```python
from rest_framework.views import exception_handler

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        original_data = response.data
        response.data = {}
        response.data['status'] = "error"
        details = original_data.get('detail', None)
        if details:
            del original_data['detail']
            response.data['message'] = str(details)
        else:
            response.data['message'] = "Invalid data"
        response.data['data'] = original_data
            
    return response
```

#### project/admin.py
Customizes the Django Admin for User and Group models using Unfold's components. Always use `ModelAdminUnfoldBase` (not raw `ModelAdmin`) for all admin classes to inherit `compressed_fields`, `warn_unsaved_form`, `sidebar_icon`, and the `edit` row action.

The full `UserAdmin`/`GroupAdmin`/`TokenAdmin` code lives in the
[[django-unfold-admin|Unfold Admin Theme]] guide (§7.1), which also documents
the required `import project.admin` in `urls.py`. Keep it there — this guide
does not duplicate it.

> **DRF-only**: `TokenAdmin` / `TokenProxy` (from `rest_framework.authtoken`) are only required if the project uses DRF's `TokenAuthentication`. If not using DRF, omit those imports, the `unregister(TokenProxy)` call, and the `TokenAdmin` class.

#### project/templates/admin/base.html
Customizes the Django Unfold admin theme by loading additional CSS and JavaScript libraries. Always extend `"admin/base.html"` — never extend `unfold/layouts/base.html` directly, as this breaks Unfold's sticky bottom bar and responsive layout logic. (The override file is `base.html`, not `base_site.html`.)
```html
{% extends "admin/base.html" %}
{% load static %}

{% block extrahead %}
{{ block.super }}
<!-- Load markdown libraries -->
<link rel="stylesheet" href="https://cdn.jsdelivr.net/simplemde/latest/simplemde.min.css" />
<link rel="stylesheet" href="{% static 'css/style.css' %}" />
<script src="https://cdn.jsdelivr.net/simplemde/latest/simplemde.min.js"></script>

<!-- Load Unfold custom scripts -->
<script src="{% static 'js/load_markdown.js' %}"></script>
{% endblock %}
```

### 11. Optional Reusable Utilities
Standalone helpers that can be imported by any app to extend functionality.

#### utils/admin_helpers.py
Logic for validating admin and support group permissions.
```python
from django.contrib.auth.models import User

def is_user_admin(user: User):
    user_grups = user.groups.all()
    user_in_admin_group = False
    for group in user_grups:
        if group.name in ["admins", "supports"]:
            user_in_admin_group = True
            break
    return user_in_admin_group or user.is_superuser
```

#### utils/automation.py
Selenium-based web automation and element selection helpers.
```python
from selenium import webdriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By

def get_selenium_elems(driver: webdriver, selectors: dict) -> dict[str, WebElement]:
    fields = {}
    for key, value in selectors.items():
        try:
            fields[key] = driver.find_element(By.CSS_SELECTOR, value)
        except Exception:
            fields[key] = None
    return fields
```

#### utils/media.py
Image processing and media URL resolution helpers.
```python
import os
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile

def get_media_url(object_or_url: object) -> str:
    url_str = ""
    if type(object_or_url) is str:
        url_str = object_or_url
    else:
        url_str = object_or_url.url

    if "s3.amazonaws.com" not in url_str and "digitaloceanspaces" not in url_str:
        host = getattr(settings, "HOST", None)
        if not host:
            return url_str
        if "://" not in host:
            return url_str
        return f"{host}{url_str}"
    return url_str

def get_test_image(image_name: str = "test.webp") -> SimpleUploadedFile:
    app_path = os.path.dirname(os.path.abspath(__file__))
    project_path = os.path.dirname(app_path)
    media_path = os.path.join(project_path, "media")

    image_path = os.path.join(media_path, image_name)
    image_file = SimpleUploadedFile(
        name=image_name,
        content=open(image_path, "rb").read(),
        content_type="image/webp",
    )
    return image_file
```

#### static/js/ Custom Scripts
The project includes several dynamic scripts in `static/js/`.

**static/js/copy_clipboard.js**
Utility for click-to-copy on elements carrying a `data-copy-url` attribute (e.g. the admin copy-link buttons).
```javascript
document.addEventListener('DOMContentLoaded', () => {
  const copyText = async (text) => {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(text)
    } else {
      // fallback: temp textarea + execCommand('copy')
    }
  }

  document.querySelectorAll('[data-copy-url]').forEach((button) => {
    button.addEventListener('click', async () => {
      try {
        await copyText(button.dataset.copyUrl)
        // briefly show "¡Copiado!" on the label, then revert
      } catch {
        // last resort: prompt() with the URL for manual copy
      }
    })
  })
})
```

**static/js/script.js**
General-purpose logic.
```javascript
// Add custom project-wide JavaScript here
```

#### Other Required Files
- **static/css/style.css**: Create an empty file for custom CSS.
- **static/logo.webp** and **static/favicon.png**: Add your project's logo and favicon. 
  > **Note:** Prompt the user to check if they have specific logo and favicon files to use, or if they would like to create placeholders or new ones now.
- **media/**: Create an empty directory in the root for local file uploads.

### 12. Database Initialization
Prepare and apply the initial database migrations, then create an administrative user.

```bash
# Create migration files for all apps
python manage.py makemigrations

# Apply migrations to the database
python manage.py migrate

# Create an administrative user
# Note: You will be prompted to enter a username, email, and password.
python manage.py createsuperuser
```

### 13. OpenSpec Setup (Gemini CLI)
Initialize and configure OpenSpec to manage project context and change proposals with Gemini CLI.

```bash
openspec init
```

After initialization, run the following command in Gemini CLI to populate your project context:

> "Please read openspec/project.md and help me fill it out with details about my project, tech stack, and conventions"

### 14. Deployment
The project is configured for containerized deployment using Docker. This setup is optimized for environments like Coolify.

#### Dockerfile
The `Dockerfile` defines the environment, installs dependencies, and prepares the application for production.

```dockerfile
# Use Python 3.12 slim image
FROM python:3.12-slim

# Set environment variables for Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container
COPY . /app/

# Ensure start script is executable
RUN chmod +x /app/start.sh

# Required ARGs and ENVs for Build-Time operations
# These must be passed via Coolify's Build Environment Variables
ARG SECRET_KEY
ARG DB_ENGINE
ARG DB_NAME
ARG DB_USER
ARG DB_PASSWORD
ARG DB_HOST
ARG DB_PORT
ARG CORS_ALLOWED_ORIGINS
ARG CSRF_TRUSTED_ORIGINS

# AWS and Storage ARGs
ARG AWS_ACCESS_KEY_ID
ARG AWS_SECRET_ACCESS_KEY
ARG AWS_STORAGE_BUCKET_NAME
ARG AWS_S3_REGION_NAME
ARG AWS_S3_ENDPOINT_URL
ARG AWS_S3_CUSTOM_DOMAIN
ARG STORAGE_AWS

# General Configuration ARGs
ARG ENV
ARG DEBUG
ARG ALLOWED_HOSTS
ARG HOST

# Stripe / deploy / tunnel ARGs (needed if referenced at build time)
ARG STRIPE_SECRET_KEY
ARG STRIPE_PUBLISHABLE_KEY
ARG STRIPE_WEBHOOK_SECRET
ARG STRIPE_API_VERSION
ARG STRIPE_PRICE_ID
ARG DEPLOY_WEBHOOK_URL
ARG COOLIFY_API_TOKEN
ARG CLOUDFLARE_TUNNEL_NAME
ARG CLOUDFLARE_TUNNEL_HOST

# Export them as ENVs so the 'RUN' commands below can see them
ENV SECRET_KEY=${SECRET_KEY} \
    DB_ENGINE=${DB_ENGINE} \
    DB_NAME=${DB_NAME} \
    DB_USER=${DB_USER} \
    DB_PASSWORD=${DB_PASSWORD} \
    DB_HOST=${DB_HOST} \
    DB_PORT=${DB_PORT} \
    CORS_ALLOWED_ORIGINS=${CORS_ALLOWED_ORIGINS} \
    CSRF_TRUSTED_ORIGINS=${CSRF_TRUSTED_ORIGINS}

ENV AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID} \
    AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY} \
    AWS_STORAGE_BUCKET_NAME=${AWS_STORAGE_BUCKET_NAME} \
    AWS_S3_REGION_NAME=${AWS_S3_REGION_NAME} \
    AWS_S3_ENDPOINT_URL=${AWS_S3_ENDPOINT_URL} \
    AWS_S3_CUSTOM_DOMAIN=${AWS_S3_CUSTOM_DOMAIN} \
    STORAGE_AWS=${STORAGE_AWS}

ENV ENV=${ENV} \
    DEBUG=${DEBUG} \
    ALLOWED_HOSTS=${ALLOWED_HOSTS} \
    HOST=${HOST}

ENV STRIPE_SECRET_KEY=${STRIPE_SECRET_KEY} \
    STRIPE_PUBLISHABLE_KEY=${STRIPE_PUBLISHABLE_KEY} \
    STRIPE_WEBHOOK_SECRET=${STRIPE_WEBHOOK_SECRET} \
    STRIPE_API_VERSION=${STRIPE_API_VERSION} \
    STRIPE_PRICE_ID=${STRIPE_PRICE_ID} \
    DEPLOY_WEBHOOK_URL=${DEPLOY_WEBHOOK_URL} \
    COOLIFY_API_TOKEN=${COOLIFY_API_TOKEN} \
    CLOUDFLARE_TUNNEL_NAME=${CLOUDFLARE_TUNNEL_NAME} \
    CLOUDFLARE_TUNNEL_HOST=${CLOUDFLARE_TUNNEL_HOST}

# Install system dependencies (e.g., for PostgreSQL support)
RUN apt-get update && apt-get install -y \
    libpq-dev gcc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first (for caching)
RUN pip install --no-cache-dir --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r requirements.txt

# Collect static files
RUN python manage.py collectstatic --noinput

# Expose the port that Django/Gunicorn will run on
EXPOSE 80

# Command to run the start script
CMD ["./start.sh"]
```

#### start.sh
The `start.sh` script handles database migrations and starts the Gunicorn server.

```bash
#!/bin/sh

# Exit immediately if a command exits with a non-zero status.
set -e

echo "Running migrations..."
# NOTE: the shipped start.sh runs `makemigrations --noinput` (generates) then
# `migrate --noinput`. Prefer `makemigrations --check` in CI to fail loudly on
# missing migrations; never rely on generated migrations at deploy time.
python manage.py makemigrations --noinput
python manage.py migrate --noinput

# Base data (reference/lookup rows) is required for the system to work.
# NOTE: do NOT run seed_loaddata here — it is environment-specific and should
# be loaded once manually.
python manage.py base_loaddata

echo "Starting Gunicorn..."
exec gunicorn --bind 0.0.0.0:80 project.wsgi:application
```
