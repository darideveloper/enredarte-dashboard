## 1. Environment & Dependencies

- [x] 1.1 Create `requirements.txt` with pinned versions (Django 5.2, DRF, django-unfold 0.77.1, django-cors-headers, django-storages, boto3, Pillow, psycopg, Whitenoise, Gunicorn, python-dotenv, requests, django-solo, django-filter, selenium)
- [x] 1.2 Create Python virtual environment (`python -m venv venv`)
- [x] 1.3 Install dependencies (`pip install -r requirements.txt`)
- [x] 1.4 Create `.env` with `ENV=dev`
- [x] 1.5 Create `.env.dev` with all dev defaults (SECRET_KEY, DEBUG=True, ALLOWED_HOSTS including enredarte.localhost, CORS_ALLOWED_ORIGINS, CSRF_TRUSTED_ORIGINS, HOST=http://localhost:8000, DB config for PostgreSQL, STORAGE_AWS=False)
- [x] 1.6 Create `.env.prod` with placeholder values (SECRET_KEY=, DEBUG=False, ALLOWED_HOSTS, HOST=, DB config, STORAGE_AWS=True, all AWS vars empty)
- [x] 1.7 Update `.gitignore` to cover Python bytecode, venv, `.env*`, SQLite dbs, staticfiles/, media/, IDE configs, macOS metadata, credentials, docs/, openspec/changes/* (not archive/)

## 2. Django Project Scaffold

- [x] 2.1 Run `django-admin startproject project .`
- [x] 2.2 Run `python manage.py startapp artworks`
- [x] 2.3 Verify `project/settings.py`, `project/urls.py`, `project/wsgi.py`, `project/asgi.py` exist
- [x] 2.4 Verify `artworks/apps.py`, `artworks/models.py`, `artworks/views.py`, `artworks/admin.py` exist

## 3. Core Settings & Configuration

- [x] 3.1 Initialize `python-dotenv` at top of `project/settings.py`: load `.env` first, get `ENV`, then load `.env.{ENV}`
- [x] 3.2 Set `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `LANGUAGE_CODE='es'`, `TIME_ZONE='America/Mexico_City'`, `USE_I18N=True`, `USE_TZ=True` from env vars
- [x] 3.3 Configure `INSTALLED_APPS`: `unfold`, `unfold.contrib.filters`, `unfold.contrib.forms`, `unfold.contrib.inlines` BEFORE `django.contrib.admin`; add `corsheaders`, `rest_framework`, `rest_framework.authtoken`, `django_filters`, `solo`, `storages`, `artworks`
- [x] 3.4 Configure `MIDDLEWARE`: `CorsMiddleware` before `CommonMiddleware`, `WhiteNoiseMiddleware` after `SecurityMiddleware`
- [x] 3.5 Configure `TEMPLATES`: add `project/templates/` to `DIRS`, register `sidebar_extras` in `libraries`, add `utils.context_processors.user_palette` to `context_processors`
- [x] 3.6 Configure dynamic database selection: PostgreSQL for dev/prod, SQLite when `sys.argv[1] == "test"` (file: `testing.sqlite3`)
- [x] 3.7 Configure `STATIC_URL='static/'`, `STATICFILES_DIRS` with `BASE_DIR/static/`, `STATIC_ROOT`, `MEDIA_URL='/media/'`, `MEDIA_ROOT`
- [x] 3.8 Configure `CORS_ALLOWED_ORIGINS` and `CSRF_TRUSTED_ORIGINS` from comma-separated env vars (strip whitespace and trailing slashes)
- [x] 3.9 Set `DATE_FORMAT="d/b/Y"`, `TIME_FORMAT="H:i"`, `DATETIME_FORMAT="d/b/Y H:i"`

## 4. Storage Backends

- [x] 4.1 Create `project/storage_backends.py` with `StaticStorage`, `PublicMediaStorage`, `PrivateMediaStorage` inheriting `S3Boto3Storage`
- [x] 4.2 Configure conditional `STORAGES` dict in `settings.py`: S3 backends when `STORAGE_AWS=True`, local `FileSystemStorage` + `CompressedManifestStaticFilesStorage` when `False`
- [x] 4.3 Configure `AWS_*` settings block in `settings.py` (gated on `STORAGE_AWS=True`): credentials, endpoint, region, project folder, compute location paths, `AWS_S3_OBJECT_PARAMETERS`, `AWS_DEFAULT_ACL=None`

## 5. DRF Configuration

- [x] 5.1 Configure `REST_FRAMEWORK` dict: `IsAuthenticated` default permission, `CustomPageNumberPagination` paginator, `PAGE_SIZE=12`, `TokenAuthentication` + `SessionAuthentication`, custom exception handler
- [x] 5.2 Create `project/pagination.py`: `CustomPageNumberPagination` extending `PageNumberPagination` with `page_size_query_param`, `max_page_size=100`, metadata-rich `get_paginated_response` (count, next, previous, page, page_size, total_pages, results)
- [x] 5.3 Create `project/handlers.py`: `custom_exception_handler` transforming responses to `{status, message, data}` format, extracting `detail` key to `message`
- [x] 5.4 Create `project/urls.py`: DRF `DefaultRouter()`, `admin/`, root redirect to admin, `api/` router include, static/media serving in debug

## 6. Unfold Admin Theme

- [x] 6.1 Define `UNFOLD` settings dict in `settings.py`: `SITE_TITLE="Enredarte Admin"`, `SITE_HEADER="Enredarte"`, `SITE_SUBHEADER="Panel de Administracion"`, `SITE_URL="/"`, `SITE_SYMBOL="palette"`, `SHOW_HISTORY=True`, `SHOW_VIEW_ON_SITE=True`, `THEME="light"`, `ENVIRONMENT="utils.callbacks.environment_callback"`, OKLCH purple color palette (50-950, hue 296)
- [x] 6.2 Configure `SIDEBAR`: `show_search=True`, `show_all_applications=True`, empty `navigation: []`
- [x] 6.3 Configure `SITE_LOGO: lambda request: static("logo.webp")`, `SITE_ICON: lambda request: static("favicon.png")`, `SITE_FAVICONS` 32x32 PNG
- [x] 6.4 Create `project/admin_base.py`: `ModelAdminUnfoldBase` extending `unfold.admin.ModelAdmin` with `compressed_fields=True`, `warn_unsaved_form=True`, `list_filter_sheet=False`, `change_form_show_cancel_button=True`, `actions_row=["edit"]`, `sidebar_icon="database"`, `edit` row action with `@action(description="Editar", permissions=["change"])`
- [x] 6.5 Create `project/admin.py`: unregister/re-register `User`, `Group`, and `TokenProxy` (DRF-only) with Unfold forms (`UserChangeForm`, `UserCreationForm`, `AdminPasswordChangeForm`), UserAdmin and GroupAdmin inheriting `BaseUserAdmin`/`BaseGroupAdmin` + `ModelAdminUnfoldBase` with `sidebar_icon`, TokenAdmin inheriting `BaseTokenAdmin` with `sidebar_icon="key"`
- [x] 6.6 Create `utils/callbacks.py`: `environment_callback` returning Spanish labels (`["Desarrollo", "info"]`, `["Produccion", "danger"]`, `["Staging", "warning"]`, `["Local", "success"]`)

## 7. Sidebar Icon Pipeline

- [x] 7.1 Create `utils/admin_icons.py`: `build_sidebar_icon_map()` iterating `admin.site._registry` for `sidebar_icon` attributes, returning `{app_label.model_name: icon_name}` dict, default `"database"`
- [x] 7.2 Create `utils/context_processors.py`: `user_palette(request)` injecting `sidebar_icons` (from `build_sidebar_icon_map`) and `user_palette_css` (empty string) into template context
- [x] 7.3 Create `utils/templatetags/__init__.py` (empty)
- [x] 7.4 Create `utils/templatetags/sidebar_extras.py`: `get_item` filter for dictionary lookups, registered as `sidebar_extras`

## 8. Template Overrides

- [x] 8.1 Create `project/templates/admin/base.html` extending `"admin/base.html"`, injecting SimpleMDE CSS/JS from CDN, `static/css/style.css`, and three JS files (`add_tailwind_styles.js`, `load_markdown.js`, `range_date_filter_es.js`) in `extrahead` block with `{{ block.super }}`
- [x] 8.2 Create `project/templates/unfold/helpers/navigation.html`: full replacement iterating `available_apps` with Unfold-styled DOM, Alpine.js accordions, `sidebar_icons|get_item:model_key|default:"database"` icon resolution, `{{ request.path }}` active state matching, fallback message for no-permission users
- [x] 8.3 Create `project/templates/unfold/helpers/navigation_user.html`: user avatar + full name + email at sidebar bottom, Alpine.js popover with theme_switch, language_switch, account_links

## 9. Static Assets

- [x] 9.1 Create `static/css/style.css`: `.editor-preview`/`.editor-preview-side` typography for headings (h1-h3), paragraphs, lists (ul/ol), blockquotes, inline code, code blocks, links — using `--color-base-*` and `--brand-primary-*` CSS variables
- [x] 9.2 Create `static/js/add_tailwind_styles.js`: `DOMContentLoaded` listener adding Tailwind classes to `.btn` and `.img-preview` elements
- [x] 9.3 Create `static/js/load_markdown.js`: `DOMContentLoaded` listener initializing SimpleMDE on all `div > textarea` with toolbar (bold, italic, heading, quote, code, link, image, unordered-list, ordered-list, undo, redo, preview), delayed 100ms
- [x] 9.4 Create `static/js/range_date_filter_es.js`: `DOMContentLoaded` listener setting Spanish placeholders on date range inputs (`created_at_from`/`updated_at_from` → "Desde", `created_at_to`/`updated_at_to` → "Hasta")
- [x] 9.5 Create `static/js/copy_clipboard.js`: `DOMContentLoaded` listener reading `copy_to_clipboard` cookie, `navigator.clipboard.writeText()`, clearing cookie after copy, stripping surrounding double-quotes
- [x] 9.6 Create `static/js/script.js`: empty placeholder file
- [x] 9.7 Create `static/logo.webp`: placeholder logo file
- [x] 9.8 Create `static/favicon.png`: placeholder favicon file

## 10. Utility Modules

- [x] 10.1 Create `utils/__init__.py` (empty)
- [x] 10.2 Create `utils/admin_helpers.py`: `is_user_admin(user)` checking membership in `["admins", "supports"]` groups or `is_superuser`
- [x] 10.3 Create `utils/media.py`: `get_media_url(object_or_url)` resolving absolute URLs (prepend `settings.HOST` for local, return as-is for S3), `get_test_image(image_name="test.webp")` returning `SimpleUploadedFile` from `media/` directory
- [x] 10.4 Create `utils/automation.py`: `get_selenium_elems(driver, selectors)` returning `{key: WebElement}` dict

## 11. Deployment Infrastructure

- [x] 11.1 Create `Dockerfile`: `python:3.12-slim`, `PYTHONDONTWRITEBYTECODE=1`, `PYTHONUNBUFFERED=1`, `WORKDIR /app`, `COPY . /app/`, `chmod +x start.sh`, all config as `ARG`/`ENV` pairs (Django DB group, AWS/Storage group, General config group), `apt-get install libpq-dev gcc`, `pip install -r requirements.txt`, `collectstatic --noinput`, `EXPOSE 80`, `CMD ["./start.sh"]`
- [x] 11.2 Create `start.sh`: `#!/bin/sh`, `set -e`, `python manage.py makemigrations --noinput`, `python manage.py migrate --noinput`, `exec gunicorn --bind 0.0.0.0:80 project.wsgi:application`
- [x] 11.3 Create `dev.sh`: check for existing tmux session `${PROJECT_NAME}_dev`, `portless proxy start`, `portless trust`, dynamic port detection starting at 8000 (ss -tuln loop), virtual env detection (venv/ or .venv/), tmux new-session running `portless enredarte --app-port $PORT -- python manage.py runserver $PORT`, attach to session

## 12. Validation & Finalization

- [x] 12.1 Create empty `media/` directory
- [x] 12.2 Run `python manage.py check` to verify configuration
- [x] 12.3 Run `python manage.py makemigrations` and `python manage.py migrate`
- [x] 12.4 Run `python manage.py createsuperuser` for initial admin access
- [x] 12.5 Run `python manage.py test` to verify test infrastructure (SQLite isolation)
- [x] 12.6 Verify admin loads at `http://localhost:8000/admin/` with Unfold theme, Spanish labels, sidebar icons, and SimpleMDE
- [x] 12.7 Verify `./dev.sh` starts correctly and app is accessible at `https://enredarte.localhost`
