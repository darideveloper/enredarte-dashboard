## Context

Enredarte is a greenfield Django project. The repository exists only with `.git`, `.gitignore`, `.opencode/` (openconfig tooling), and `openspec/` scaffolding. No Python code, no Django project, no configuration. This change establishes the entire foundation — following identical conventions to existing Django projects documented in the internal knowledge base — before any feature or model development begins.

The knowledge base prescribes a specific stack and pattern: environment-variable-first config via `python-dotenv`, `django-unfold` for a modern admin, Django REST Framework for APIs, `django-storages` for cloud storage, Docker for deployment, and `portless` + `tmux` for local development with subdomains.

**Constraints:**
- Admin interface must be fully Spanish (all visible text)
- No Celery, no Redis, no email — simpler deployment profile
- PostgreSQL for development, SQLite for testing
- S3 storage backends must be defined but inactive by default (`STORAGE_AWS=False`)

## Goals / Non-Goals

**Goals:**
- Complete, runnable Django 5.2 project with `./dev.sh` and `python manage.py runserver`
- Spanish-localized Unfold admin with permission-aware auto sidebar, markdown editor, date filters, and Tailwind enhancements
- DRF API foundation with custom pagination and standardized error format
- Storage layer that switches between local and S3 via single env var
- Docker build that succeeds (including `collectstatic`) for Coolify deployment
- Cookie-based image copy link utility for future media models

**Non-Goals:**
- No application models, views, serializers, or API endpoints (only scaffold)
- No database migrations beyond Django's built-in contrib apps
- No Celery workers, Redis caching, or Stripe webhooks
- No email configuration
- No actual S3/DigitalOcean bucket provisioning (only code readiness)

## Decisions

### Decision 1: `.env` as pure selector vs flat `.env` with all config

**Chosen:** `.env` contains ONLY `ENV=dev`. All config lives in `.env.dev` and `.env.prod`, duplicated per environment.

**Rationale:** The internal docs enforce this pattern across all projects. It prevents accidental cross-environment leaks (e.g., prod secrets in dev), works cleanly with Coolify's build env vars, and makes it obvious which config belongs to which environment. The alternative — a single `.env` with all vars defaulted to dev — leads to confusion about what runs where.

### Decision 2: `django-unfold` with auto-render sidebar vs manual navigation list

**Chosen:** Permission-aware auto sidebar (`show_all_applications: True`, `navigation: []`) with a template override at `project/templates/unfold/helpers/navigation.html`.

**Rationale:** Adding a new `ModelAdmin` requires zero config changes — the sidebar auto-populates from registered admins and filters by user permissions. The manual navigation list would require updating `settings.py` every time a model is added, which is error-prone as the project grows. The template override ensures Unfold-styled rendering (Unfold's own fallback to Django's `admin/app_list.html` produces unstyled, boxed-table markup).

### Decision 3: PostgreSQL for dev, SQLite for testing

**Chosen:** Dynamic DB selection based on `IS_TESTING` flag (checks `sys.argv[1] == "test"`).

**Rationale:** Matches the internal docs. PostgreSQL is the production target, so dev must mirror it. SQLite for `manage.py test` provides instant database creation/destruction without requiring a running postgres server. No separate test config needed.

### Decision 4: S3 storage classes defined but inactive

**Chosen:** `storage_backends.py` with all three backends (`StaticStorage`, `PublicMediaStorage`, `PrivateMediaStorage`) exists from day one, but `STORAGE_AWS=False` in `.env.dev` falls back to local `FileSystemStorage`.

**Rationale:** The code is deployment-ready without any changes when switching to S3. Teams don't need to remember to create storage classes later. The `STORAGES` dict (Django 4.2+) makes the switch clean.

### Decision 5: No custom `AdminSite` subclass — template overrides instead

**Chosen:** Override `admin/base.html` (extending `"admin/base.html"` — never `unfold/layouts/base.html`), `unfold/helpers/navigation.html`, and `unfold/helpers/navigation_user.html` via Django's template loader resolution. This follows the proven pattern from the `clients` production project.

**Rationale:** Extending `"admin/base.html"` preserves Unfold's sticky bottom bar and responsive layout logic. Extending `unfold/layouts/base.html` directly is explicitly warned against in the Unfold docs. The clients project has validated this approach in production. Template overrides require no `AdminSite` subclassing or URLconf changes.

### Decision 6: Vanilla Django `dev.sh` — no Celery/Redis windows

**Chosen:** Case A (vanilla Django) from the local subdomain setup guide: one tmux window running `portless enredarte --app-port $PORT -- python manage.py runserver $PORT`.

**Rationale:** No background task infrastructure is needed at this stage. The `dev.sh` can be extended later with worker/beat windows when Celery is added. Starting simple avoids dangling tmux windows that consume resources for no purpose.

## Risks / Trade-offs

- **[Risk] Image copy link utility has no model to attach to** → Mitigation: The `copy_clipboard.js` and `get_media_url()` utility are created now. The `@action` decorator on a `ModelAdmin` is noted in tasks as ready for any future model with an image field.
- **[Risk] `portless` and `tmux` must be pre-installed** → Mitigation: `dev.sh` checks for required tools on launch. This is documented in the setup guide prerequisites.
- **[Risk] Docker build requires all env ARGs even for local storage** → Mitigation: `start.sh` and Dockerfile pass all ARGs. When `STORAGE_AWS=False`, the S3 ARGs can be empty strings — the conditional storage code in `settings.py` doesn't read them.

## Open Questions

<!-- None — all design decisions resolved during brainstorming -->
