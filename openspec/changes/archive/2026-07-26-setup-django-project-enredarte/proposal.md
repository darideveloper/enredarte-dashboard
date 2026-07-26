## Why

Scaffold the complete Django production-ready foundation for Enredarte — a new project with nothing but git and openspec initialized. The setup follows established conventions documented in the internal Django knowledge base, ensuring consistency across all projects. Without this foundation, no feature work, admin interface, or API development can proceed.

## What Changes

- Create the full Django 5.2 project scaffold with `project/` configuration module and `artworks` initial app
- Set up environment-variable-first configuration via `python-dotenv` with `.env` as pure selector (`.env.dev` / `.env.prod`)
- Configure PostgreSQL for dev, SQLite for testing, with dynamic backend switching
- Integrate `django-unfold` admin theme with full Spanish localization — all visible admin text (site title, header, sidebar groups, model verbose names, help texts) in Spanish
- Wire Django REST Framework with Token + Session auth, custom pagination, standardised error handling
- Set up storage backends: local `FileSystemStorage` for dev, S3-ready `django-storages` classes for production (conditional on `STORAGE_AWS`)
- Deploy infrastructure: multi-stage Dockerfile with build-time `collectstatic`, `start.sh` for Coolify, and `dev.sh` for local development via `portless` + `tmux` (https://enredarte.localhost)
- Admin utilities: `project/admin_base.py` with `ModelAdminUnfoldBase`, image copy link (cookie-based clipboard), SimpleMDE markdown editor, Spanish date range filter placeholders, Tailwind class injection, permission-aware auto sidebar with icon mapping (including sidebar icon pipeline: `admin_icons.py`, `context_processors.py`, `templatetags/sidebar_extras.py`), and `navigation_user.html` template override
- Placeholder logo/favicon, empty `style.css`, empty `script.js`, and `media/` directory
- Utilities: `utils/admin_helpers.py` (`is_user_admin`), `utils/automation.py` (Selenium), `utils/media.py` (URL resolution, test image)

## Capabilities

### New Capabilities

- `django-core`: Project scaffold — `project/` module, `artworks` app, environment infrastructure (`.env` selector + `.env.dev`/`.env.prod`), dynamic database config (PostgreSQL/SQLite), static/media configuration, CORS/CSRF from env vars
- `unfold-admin`: Django Unfold admin theme — custom `UNFOLD` settings dict with OKLCH colors, Spanish text for all visible UI elements, permission-aware auto sidebar with icon mapping, `User`/`Group` registration with Unfold forms (`TokenProxy` too if using DRF auth), `ModelAdminUnfoldBase` base class (`sidebar_icon`, `compressed_fields`, `warn_unsaved_form`, `edit` action), SimpleMDE markdown integration, Spanish date range filter placeholders, Tailwind class injection, markdown preview CSS
- `rest-api`: Django REST Framework — DRF router setup in root URLconf, `CustomPageNumberPagination` with metadata-rich responses (page/total_pages/page_size), custom exception handler (`status`/`message`/`data` format), Token + Session authentication, global date format `d/b/Y H:i`
- `media-storage`: Storage backends — `StaticStorage`/`PublicMediaStorage`/`PrivateMediaStorage` S3 classes, conditional `STORAGES` dict toggled via `STORAGE_AWS` env var, `get_media_url()` utility for absolute URL resolution, image copy link feature (server cookie → client clipboard via `navigator.clipboard.writeText`)
- `deployment`: Container + local dev infrastructure — multi-stage `Dockerfile` (Python 3.12-slim, build-time ARGs for `collectstatic` with S3), `start.sh` (auto-migrate + Gunicorn on port 80), `dev.sh` with `portless` + `tmux` for unified local development at `https://enredarte.localhost`

### Modified Capabilities

<!-- No existing capabilities to modify — greenfield project -->

## Impact

- **New repo scaffold**: 40+ files created across project root, `project/`, `artworks/`, `static/`, `utils/`, `project/templates/`
- **Dependencies added**: Django 5.2, DRF, django-unfold 0.77.1, django-cors-headers, django-storages, boto3, Pillow, psycopg, Whitenoise, Gunicorn, python-dotenv, requests, django-solo, django-filter, selenium (E2E), SimpleMDE (CDN)
- **Infrastructure**: Portless proxy for local dev, Docker for Coolify deployment
- **No database migrations yet**: Models not created in this change — only the project skeleton and `artworks` app scaffold
