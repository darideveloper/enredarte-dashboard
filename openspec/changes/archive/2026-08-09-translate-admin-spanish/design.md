## Context

The admin runs on django-unfold 0.97.0 over Django 5.2. `project/settings.py` already sets `LANGUAGE_CODE = "es"`, `USE_I18N = True`, `LANGUAGES = [("es", "Español"), ("en", "English")]`, and places `unfold` before `django.contrib.admin` in `INSTALLED_APPS`. This means Django's shipped Spanish catalogs (`django/conf/locale/es` + `django/contrib/admin/locale/es`) already translate the generic chrome: buttons (Guardar/Eliminar), pagination, delete confirmations, login, date widgets.

The gaps are entirely in project-owned strings (Source B–C of `docs/django-i18n-es-admin.md`) and in django-unfold-only strings (Source §9). Verified by introspection:

- Every model field uses an auto-generated English `verbose_name` ("created at", "is active", "sort order", "birth year", "price mxn", …) because no explicit `verbose_name` is set — including on the abstract bases `TimeStampedModel`, `BaseModel`, `TranslationBase`, `Person`, so it affects all 23 concrete models.
- `Artist`, `ArtCurator`, `Gallery`, `Artwork` lack `Meta.verbose_name(_plural)` → "artist"/"artists", "art curator"/"art curators", "gallery"/"gallerys", "artwork"/"artworks".
- `ArtworkStatus` and `ArtistSocialLink.Platform` choice labels are English.
- `core`/`artworks` `AppConfig` have no `verbose_name` → sidebar shows "Core"/"Artworks".
- `artworks/admin.py` fieldset titles are English; `project/admin_base.py` row action is `description="Edit"`.
- Unfold ships no Spanish catalog (`unfold/locale` does not exist). A `gettext` check against both Django `es` catalogs confirms **40** unfold `{% trans %}` msgids are untranslated (sidebar search, filters, login/confirm text, misc UI).

No `LocaleMiddleware` and no per-request language switching are desired — the admin is Spanish-only (per the reference doc §2).

## Goals / Non-Goals

**Goals:**
- Every admin-facing string renders in Spanish: model labels, app names, fieldset titles, action descriptions, choice badges/dropdowns, and all unfold chrome.
- Follow the reference doc architecture: hard-coded Spanish literals for project strings (Sources B–D) + a single small `LOCALE_PATHS` catalog for the ~40 unfold-only msgids (Source §9).
- Keep DB values language-free (English choice values, unchanged slugs).
- Generate migrations so the data model stays consistent.

**Non-Goals:**
- Translating the public website / API responses (admin-only scope).
- Multi-language admin, `LocaleMiddleware`, language switch UI (rejected: Spanish-only).
- Translating strings that Django's shipped `es` catalog already covers.
- Renaming model classes, fields, DB columns, or URL paths (only display labels change).
- Localizing `SITE_TITLE`/`SITE_HEADER` brand text ("Enredarte Admin" / "ENREDARTE DASHBOARD").

## Decisions

**D1. Literal Spanish `verbose_name` on every field, including abstract bases.**
Set `verbose_name` once on the abstract base classes (`TimeStampedModel`, `BaseModel`, `TranslationBase`, `Person`) so `created_at`, `slug`, `is_active`, `sort_order`, `language`, `name`, `email`, `website`, `photo` are inherited by all concrete models. Concrete-only fields get `verbose_name` on each model.
*Alternative considered*: a custom `BaseModel` mixin that auto-capitalizes field names — rejected, fragile and doesn't handle multi-word names well; literal Spanish is the doc's pattern.

**D2. `Meta.verbose_name`/`verbose_name_plural` for the 4 missing models.**
`Artist` → "Artista"/"Artistas", `ArtCurator` → "Curador de arte"/"Curadores de arte", `Gallery` → "Galería"/"Galerías", `Artwork` → "Obra de arte"/"Obras de arte". Other taxonomy models already have Spanish Meta.

**D3. Spanish choice labels, English values.**
`ArtworkStatus`: values stay `available|sold|reserved|on_loan|not_available`, labels → `Disponible|Vendida|Reservada|En préstamo|No disponible`. `ArtistSocialLink.Platform`: values unchanged, label `OTHER = "other", "Otra"` (brand names Instagram/Facebook/etc. stay). This keeps the DB and any external consumers stable.

**D4. `AppConfig.verbose_name` in Spanish.**
`CoreConfig` → `verbose_name = "Principal"` (future-proofing — `core` currently has no registered admin models, so this is a no-op until core registers models), `ArtworksConfig` → `verbose_name = "Obras"`. The sidebar groups by `app.name`.

**D5. Localize admin definitions directly.**
Translate fieldset titles in `artworks/admin.py` (e.g. "Personal Info" → "Datos personales", "System Status" → "Estado del sistema", "Main Attributes" → "Atributos principales", "Commercial & Status" → "Comercial y estado", "System Settings" → "Configuración del sistema", "System Info" → "Información del sistema", "Basic Info" → "Información básica", "Contact & Media" → "Contacto y medios") and the row action in `project/admin_base.py` `description="Edit"` → `"Editar"`.

**D6. A project `locale/` catalog ONLY for unfold-only msgids.**
Add `LOCALE_PATHS = [BASE_DIR / "locale"]` and create `locale/es/LC_MESSAGES/django.po` **by hand** with exactly the 40 unfold-only msgids + Spanish msgstrs. Do **not** run `makemessages` — it would scan all installed-app templates (unfold has 202 HTML files) and collect ~85 msgids, including ~45 already covered by Django's `es` catalog. Empty-msgstr entries that get compiled into the `.mo` would override Django's translations with blank strings. Django merges project + shipped catalogs, so base chrome keeps working and we never duplicate it.
*Alternative considered*: copying ~20 unfold templates into `templates/unfold/` with literal Spanish (doc §9 option 1) — rejected: the catalog is one file, survives unfold upgrades, and covers all 40 strings uniformly.

**D7. Zero-data migration.**
`verbose_name` changes are metadata-only; `makemigrations` produces a no-op data migration. Choice label changes do **not** generate migrations (only `choices` on a field does not trigger one) — so only field `verbose_name` edits produce migrations.

## Risks / Trade-offs

- [Catalog misses an unfold msgid after an unfold upgrade] → The `.po` documents the source: re-grep `unfold/templates` for `{% trans %}` ids not in Django's `es` catalog and add any new ones.
- [Accidentally overriding Django strings by leaving non-unfold entries in the `.po`] → `makemessages` collects ALL msgids from installed-app templates (~85), not just unfold. Entries with empty `msgstr` that get compiled into the `.mo` would override Django's shipped catalog with empty strings, making those buttons/labels blank. Mitigation: the `.po` is created by hand with exactly the 40 msgids; `makemessages` is **not** run on the project.
- [Choice-label/`verbose_name` edits surprising consumers reading `_meta.verbose_name`] → Confirmed no code reads `verbose_name` for logic; display only. Choices values unchanged, so DB/external data unaffected.
- [Migration churn] → One zero-data migration; safe, per the reference doc's pitfalls note.
- [GNU gettext not available in the environment] → `compilemessages` needs `msgfmt`. Already installed in this development environment; add `gettext` to the Dockerfile if the CI/deploy environment lacks it.

## Migration Plan

1. Apply code edits (models, apps, admin, settings).
2. `python manage.py makemigrations` → review the generated migration (fields only, no data ops) → `migrate`.
3. Create `locale/es/LC_MESSAGES/django.po` by hand with the 40 unfold-only msgstrs + `compilemessages`.
4. Restart the dev server; verify admin renders Spanish and that `Save`/`Delete`/pagination still come from Django (not duplicated in our catalog).

Rollback: revert the code edits and delete the `locale/` dir + generated migration; the admin returns to the current English-label state.

## Open Questions

None blocking. (`SITE_TITLE`/`SITE_HEADER` branding is intentionally left as-is per Non-Goals.)
