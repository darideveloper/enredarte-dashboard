## Why

A full audit of the 11 files under `docs/` found internal inconsistencies: four documents exist but are missing from the `django.md` hub, `django-project-setup.md` and `django-media-storage.md` disagree on storage/docker settings that would fail at runtime if followed verbatim, `django-project-setup.md` and `django-unfold-admin.md` duplicate `project/admin.py` code and disagree on `urls.py` wiring, `django-drf.md` uses a different project name and an invalid `choices` style, and several formatting/link conventions diverge across files. The docs are the project's source of truth for setup and conventions, so the inconsistencies must be resolved in one coherent pass.

## What Changes

- Add the four missing links (`django-fixtures`, `django-redis`, `django-local-subdomain-setup`, `django-i18n-es-admin`) to the `django.md` hub.
- Define `STATIC_LOCATION`, `PUBLIC_MEDIA_LOCATION`, `PRIVATE_MEDIA_LOCATION` in `django-project-setup.md` Step 7's S3 branch and cross-reference `django-media-storage.md`.
- Add a `private` backend (local `FileSystemStorage` under a `private-media/` subfolder) to the local `STORAGES` fallback in `django-project-setup.md`.
- Add the missing `AWS_S3_REGION_NAME`, `AWS_S3_CUSTOM_DOMAIN`, `AWS_PROJECT_FOLDER` ARGs to the Docker snippet in `django-media-storage.md`.
- Add `python manage.py base_loaddata` (with a comment) to `start.sh` in `django-project-setup.md` after `migrate`.
- Replace `python manage.py makemigrations --noinput` with `makemigrations --check --noinput` in `start.sh` and add a note to run `makemigrations` locally before building the image.
- Add `import project.admin` (with a comment) to `urls.py` in `django-project-setup.md`.
- Move the canonical `project/admin.py` code into `django-unfold-admin.md` only; replace the copy in `django-project-setup.md` Step 10 with a reference to it.
- Rename `myproject` → `project` throughout `django-drf.md`; replace the sample model's `LANGS` dict with a `models.TextChoices` subclass.
- Remove the `range_date_filter_es.js` script tag from the `admin/base.html` template in `django-project-setup.md` and document it in `django-i18n-es-admin.md` instead.
- Align the logo filename to `logo.webp` in `django-project-setup.md` Step 11 (matching `django-unfold-admin.md`).
- Fix the orphaned sentence outside the code fence in `django-unfold-admin.md` §3.1 (move inside the block as a comment).
- Normalize `django-redis.md` wiki links: short-form `[[name|label]]` for docs in this folder, plain text labels for external refs.
- Add a wikilink portability convention section to `docs/django.md` explaining how agents must handle `[[wikilinks]]` when copying docs into new Django projects (short-form links stay as-is, vault-path links to sibling docs convert to short-form, external `30-resources/*` links become plain text labels).
- No changes to the codebase, models, or runtime behavior — docs only.

## Capabilities

### New Capabilities

- `docs-hub-completeness`: the `django.md` hub indexes every document in `docs/` so the note graph has no missing entry points, and documents the wikilink portability convention for agents copying docs into new projects.
- `docs-config-coherence`: setup docs agree on storage locations, the private storage backend, Docker build ARGs, project naming, model choices style, logo filename, and where Spanish-only assets belong.
- `docs-deploy-admin-coherence`: entrypoint and admin wiring docs agree — `base_loaddata` runs at container start, `makemigrations` validates instead of generating in prod, `project.admin` is imported in `urls.py`, and `project/admin.py` has a single canonical copy.
- `docs-formatting`: code-fence boundaries and wiki-link conventions are consistent across all files.

### Modified Capabilities

- None.

## Impact

- **Code**: none — documentation files only (`docs/*.md`).
- **Docs affected**: `django.md`, `django-project-setup.md`, `django-drf.md`, `django-unfold-admin.md`, `django-i18n-es-admin.md`, `django-media-storage.md`, `django-redis.md`.
- **Risk**: low — pure prose/code-sample edits; no runtime or migration impact.
- **Out of scope (reviewed, intentionally kept)**: the `openspec-ignoring-proposals` and `coolify-services.md` references resolve via the external Obsidian vault and are deliberately left as external refs.
