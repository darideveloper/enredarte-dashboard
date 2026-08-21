## Why

21 concrete models lack a meaningful `__str__`: 10 translation rows fall back to Django's default (`"DisciplineTranslation object (1)"`), and 11 others — the 7 content models, `Artwork`, and the 3 join models — return raw slugs (`"guadalajara"`, `"oleo"`) instead of their Spanish names/titles. The admin's M2M widgets (`filter_horizontal`) and related dropdowns render via `__str__`, so the Artwork change form currently shows `pintura`/`oleo` instead of `Pintura`/`Óleo`.

## What Changes

- Add a reusable abstract mixin `TranslatableName` in `core/models.py` providing `translated_name()` (prefers Spanish `es`, falls back to any language, then to slug) and `__str__`.
- Apply the mixin to the 7 content models whose display name lives in translations: `Location`, `Gallery`, `Discipline`, `Technique`, `Theme`, `Format`, `Scale`.
- Add `Artwork.translated_title()` and `__str__` using the Spanish title (same preference/fallback logic).
- Add `__str__` to all 10 translation models in the form `"{parent} ({language})"` (e.g. `"Guadalajara (es)"`).
- Add content-based `__str__` to the join models:
  - `ArtistSocialLink` → `"{platform} — {artist}"` (e.g. `"Instagram — Frida Kahlo"`)
  - `ArtworkGallery` → `"{artwork} en {gallery}"`
  - `ArtworkImage` → `alt_es` when set, else `"Imagen de {artwork}"`
- `Artist` and `ArtCurator` keep the inherited `Person.__str__` (name); no change.
- Add tests covering Spanish preference, fallback, and join-model strings.
- Update `docs/django-i18n-es-admin.md` Step 2 to document the translated-model `__str__` convention (`TranslatableName` / `translated_name()` Spanish-first lookup); the doc currently only shows the direct `return self.name` pattern.

## Capabilities

### New Capabilities
- `model-spanish-str`: All concrete models expose a Spanish, content-based `__str__`.

### Modified Capabilities
<!-- None: admin display_name helpers and all existing spec requirements are unchanged. -->

## Impact

- `core/models.py`: new abstract mixin `TranslatableName`.
- `artworks/models.py`: `TranslatableName` mixin on 7 content models + `__str__`/`translated_title` on 14 models (Artwork, 10 translations, 3 joins).
- `artworks/tests.py`: new `ModelStrTestCase`.
- `docs/django-i18n-es-admin.md`: Step 2 gains the translated-model `__str__` convention. Other docs (fixtures, unfold, etc.) are unaffected — their `__str__` examples use direct-name models.
- No migrations (Python-only change).
- Performance note: `__str__` now queries `translations` (previously slug-only). N+1 on the Artwork `filter_horizontal` widgets (~36 taxonomy rows) is negligible at this scale.
