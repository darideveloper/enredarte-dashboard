## ADDED Requirements

### Requirement: Environment-first configuration
The system SHALL load configuration from environment files where `.env` is a pure selector containing only `ENV=dev` or `ENV=prod`, and the environment-specific file `.env.{ENV}` contains all actual configuration values. The `.env.dev` and `.env.prod` files SHALL be created with all required variables and sensible development defaults, including `HOST=http://localhost:8000` in dev (used by `get_media_url` for absolute URL generation) and `HOST=` (placeholder) in prod.

#### Scenario: Development environment loads correctly
- **WHEN** `ENV=dev` is set in `.env`
- **THEN** `load_dotenv` must load `.env.dev` and `DEBUG=True`, `STORAGE_AWS=False`, `HOST=http://localhost:8000`, and `ALLOWED_HOSTS=localhost,127.0.0.1,enredarte.localhost` are resolved from env vars

#### Scenario: Production environment loads correctly
- **WHEN** `ENV=prod` is set in `.env`
- **THEN** `load_dotenv` must load `.env.prod` and `DEBUG=False`, `STORAGE_AWS=True`, and `HOST` SHALL be empty (to be filled at deploy time)

#### Scenario: Missing ENV fallback
- **WHEN** `.env` is missing or `ENV` is unset
- **THEN** the system SHALL default to `dev` environment

### Requirement: Django project scaffold
The system SHALL create a Django project named `project` with `django-admin startproject project .` and an initial app named `artworks` via `python manage.py startapp artworks`.

#### Scenario: Project module exists
- **WHEN** the project is initialized
- **THEN** `project/settings.py`, `project/urls.py`, `project/wsgi.py`, `project/asgi.py` must exist at the project root level

#### Scenario: Artworks app exists
- **WHEN** the app is created
- **THEN** `artworks/apps.py`, `artworks/models.py`, `artworks/views.py`, `artworks/admin.py` must exist

### Requirement: Dynamic database selection
The system SHALL use PostgreSQL for development and production environments, and SQLite when running tests (`sys.argv[1] == "test"`). Database connection parameters SHALL be read from environment variables (`DB_ENGINE`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`).

#### Scenario: Development uses PostgreSQL
- **WHEN** `DB_ENGINE=django.db.backends.postgresql` and the command is NOT `test`
- **THEN** the database connection SHALL target PostgreSQL with credentials from environment variables

#### Scenario: Test runner uses SQLite
- **WHEN** `python manage.py test` is executed
- **THEN** the database SHALL be SQLite with the database file at `testing.sqlite3`, independent of `DB_ENGINE` env var

### Requirement: Static and media file configuration
The system SHALL configure `STATIC_URL='static/'`, `MEDIA_URL='/media/'`, `STATICFILES_DIRS` including `BASE_DIR/static/`, `STATIC_ROOT` as `BASE_DIR/staticfiles`, and `MEDIA_ROOT` as `BASE_DIR/media`. The `media/` directory SHALL be created as an empty folder.

#### Scenario: collectstatic works locally
- **WHEN** `python manage.py collectstatic --noinput` is run with `STORAGE_AWS=False`
- **THEN** static files SHALL be collected into `staticfiles/` using Whitenoise's `CompressedManifestStaticFilesStorage`

#### Scenario: Media files served in development
- **WHEN** `DEBUG=True`
- **THEN** `urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)` SHALL serve media files from `MEDIA_ROOT`

### Requirement: CORS and CSRF from environment
The system SHALL parse comma-separated `CORS_ALLOWED_ORIGINS` and `CSRF_TRUSTED_ORIGINS` from environment variables, stripping whitespace and trailing slashes from each origin. Empty or `None` values SHALL result in empty lists.

#### Scenario: Multiple origins parsed
- **WHEN** `CORS_ALLOWED_ORIGINS=http://localhost:4321,http://127.0.0.1:8000`
- **THEN** `CORS_ALLOWED_ORIGINS` list SHALL contain both origins with trailing slashes stripped

#### Scenario: None value handled
- **WHEN** `CORS_ALLOWED_ORIGINS=None` or is unset
- **THEN** the cors_allowed variable SHALL NOT be assigned (no `CORS_ALLOWED_ORIGINS` in settings)

### Requirement: Installed apps and middleware registration
The system SHALL register `corsheaders`, `rest_framework`, `rest_framework.authtoken`, `django_filters`, `solo`, `storages`, and `artworks` in `INSTALLED_APPS`. Middleware SHALL include `CorsMiddleware` (before `CommonMiddleware`) and `WhiteNoiseMiddleware` (after `SecurityMiddleware`).

#### Scenario: All apps present
- **WHEN** `python manage.py check` runs
- **THEN** no import errors for `corsheaders`, `rest_framework`, `django_filters`, `solo`, `storages`, or `artworks`

### Requirement: Global URL configuration
The system SHALL configure root URLconf with admin at `admin/`, root redirect to admin (`RedirectView.as_view(url='/admin/')`), DRF router at `api/`, and static/media serving in debug mode.

#### Scenario: Root redirect to admin
- **WHEN** browser navigates to `/`
- **THEN** it SHALL redirect to `/admin/`

#### Scenario: API router accessible
- **WHEN** browser navigates to `/api/`
- **THEN** DRF router's default API root view SHALL render (even with empty router)

### Requirement: Spanish localization for Django
The system SHALL set `LANGUAGE_CODE='es'` in settings so that Django's built-in form validation, model field names, and error messages render in Spanish.

#### Scenario: Django uses Spanish
- **WHEN** `LANGUAGE_CODE='es'` is set and a built-in form error occurs (e.g., required field missing)
- **THEN** the error message SHALL render in Spanish (e.g., "Este campo es obligatorio." instead of "This field is required.")

### Requirement: Admin helpers utility
The system SHALL create `utils/admin_helpers.py` with an `is_user_admin(user)` function that returns `True` if the user belongs to a group named `"admins"` or `"supports"`, or is a superuser.

#### Scenario: Admin group member identified
- **WHEN** a user belongs to the "admins" group
- **THEN** `is_user_admin(user)` SHALL return `True`

#### Scenario: Regular user not identified as admin
- **WHEN** a user does NOT belong to "admins" or "supports" groups and is NOT superuser
- **THEN** `is_user_admin(user)` SHALL return `False`

### Requirement: Placeholder JavaScript file
The system SHALL create `static/js/script.js` as an empty placeholder for future project-wide JavaScript.

#### Scenario: File exists
- **WHEN** the project scaffold is complete
- **THEN** `static/js/script.js` SHALL exist

### Requirement: Timezone configuration
The system SHALL set `TIME_ZONE='America/Mexico_City'`, `USE_I18N=True`, and `USE_TZ=True`.

#### Scenario: Timezone applied
- **WHEN** a datetime is stored and retrieved
- **THEN** it SHALL be stored in UTC and displayed in `America/Mexico_City` timezone

### Requirement: Gitignore configuration
The system SHALL ensure a `.gitignore` exists covering: Python bytecode (`__pycache__`, `*.pyc`), virtual environments (`venv`), env files (`.env*`), SQLite databases (`*.sqlite3`), `staticfiles/`, `media/`, IDE configs (`.vscode`, `.windsurf`), macOS metadata (`.DS_Store`), credentials, `docs/`, and `openspec/changes/*` (excluding `openspec/changes/archive/`). Existing `.gitignore` entries for `.opencode/` agents SHALL be preserved in the final merge.

#### Scenario: Sensitive files excluded
- **WHEN** `git add .` is run
- **THEN** `.env.dev`, `.env.prod`, `venv/`, `*.sqlite3`, `staticfiles/`, `media/` SHALL NOT be staged
