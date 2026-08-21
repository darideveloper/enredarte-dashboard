## Why

The Django admin is a Spanish-market product but most admin-facing strings render in English: model field labels and model names use auto-generated English names, app names show "Core"/"Artworks", several fieldset titles and one row action are English, and ~40 django-unfold-only strings (sidebar search, filters, login) are untranslated. `LANGUAGE_CODE = "es"` is already set, so Django's shipped Spanish chrome works — but the project-owned labels and the Unfold strings still leak English.

## What Changes

- Add Spanish `verbose_name` to every model field (including the abstract bases `TimeStampedModel`, `BaseModel`, `TranslationBase`, `Person` so it cascades to all concrete models).
- Add `Meta.verbose_name` / `Meta.verbose_name_plural` in Spanish to `Artist`, `ArtCurator`, `Gallery`, `Artwork` (the four models currently showing English names).
- Translate English choice labels to Spanish for `ArtworkStatus` ("Available" → "Disponible", etc.) and `ArtistSocialLink.Platform` ("Other" → "Otra"); DB values stay English.
- Add Spanish `verbose_name` to `CoreConfig` and `ArtworksConfig` app configs. When the `core` app gains admin models the sidebar/index will show "Principal" instead of "Core"; `artworks` immediately shows "Obras" instead of "Artworks".
- Translate English fieldset titles in `artworks/admin.py` and the `Edit` row-action description in `project/admin_base.py`.
- Add a project `locale/` catalog (`LOCALE_PATHS`) covering the ~40 django-unfold-only msgids that are not in Django's shipped Spanish catalog (sidebar search, filters, login/confirm dialogs, misc UI). This merges with Django's catalog; it does not replace it.
- Generate a migration for the `verbose_name` changes (zero-data migration) and a `.mo` catalog via `compilemessages`.

## Capabilities

### New Capabilities

- `admin-spanish-labels`: Spanish literal labels across models, app configs, and admin definitions (Source B–C in the i18n reference) — field `verbose_name`, `Meta.verbose_name(_plural)`, choice labels, app `verbose_name`, fieldset titles, action descriptions.
- `unfold-spanish-catalog`: A project-level `LOCALE_PATHS` translation catalog that provides Spanish `msgstr`s for the django-unfold-only `{% trans %}` msgids that Django's shipped `es` catalog does not cover.

### Modified Capabilities

<!-- No existing spec-level behavior changes. -->

## Impact

- `core/models.py` — add `verbose_name` to abstract base fields.
- `artworks/models.py` — add field `verbose_name`s, `Meta.verbose_name(_plural)` for 4 models, Spanish choice labels.
- `core/apps.py`, `artworks/apps.py` — add `verbose_name`.
- `artworks/admin.py`, `project/admin_base.py` — Spanish fieldset titles / action description.
- `project/settings.py` — add `LOCALE_PATHS = [BASE_DIR / "locale"]`.
- New `locale/es/LC_MESSAGES/django.po` (+ compiled `.mo`) — the Unfold catalog.
- New migration(s) from `makemigrations` (zero-data).
- No public-site or API behavior changes; admin-only scope.
