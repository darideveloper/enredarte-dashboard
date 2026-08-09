## Why

The public artist profile page will render ten content blocks, but the current `Artist`/`Artwork` models only back three of them (bio, artwork list, taxonomy data). Social links, location, highlighted works, and a views counter do not exist in the data layer, and the derived blocks (techniques, available works, new additions, most viewed, curations) have no reusable computation. This change prepares the model + admin layer so the profile blocks are backed by real data, with calculations living on the models so the future DRF API and the admin share one source of truth.

## What Changes

**Models** (`artworks/models.py`):

- Add `ArtistSocialLink` model (`BaseModel`): `artist` FK, `platform` (TextChoices: Instagram, Facebook, X, TikTok, LinkedIn, YouTube, Behance, Other), `url`, `sort_order`.
- Add `Location` model (`BaseModel`) + `LocationTranslation` (`TranslationBase`, es/en name, `unique_together`) following the existing taxonomy pattern.
- Add `Artist.location` FK (`SET_NULL`, nullable, `related_name="artists"`) — one location shared by many artists.
- Add `Artwork.is_highlighted` (`BooleanField`, default `False`).
- Add `Artwork.views_count` (`PositiveIntegerField`, default `0`, editable in admin while no API exists to auto-increment).
- Add derived, reusable properties on `Artist`: `techniques`, `available_artworks`, `new_additions`, `highlighted_artworks`, `most_viewed`, `curations` (galleries exhibiting the artist's works). These return QuerySets so admin and future DRF serializers both consume them.
- "Más vendidos" is explicitly deferred (depends on the future sales app) — no model change.

**Fixtures** (follow the existing base/seed fixture pattern and the `base_loaddata`/`seed_loaddata` loader — required so demo artists ship with a location and social links, and so the admin has locations to assign):

- New base fixtures `Location.json` + `LocationTranslation.json` (4 stable-PK locations, es/en; exact manifest in `specs/artist-location/spec.md`).
- New seed fixture `ArtistSocialLink.json` (demo links) and update `Artist.json` seed rows with a `location`.

**Admin** (`artworks/admin.py`):

- `ArtistSocialLinkInline` (`TabularInline`) on `ArtistAdmin` (platform, url, sortable).
- `LocationAdmin` + `LocationTranslationInline` mirroring the taxonomy admins (Spanish labels "Ubicación").
- `ArtistAdmin`: `location` field; new readonly "Resumen" fieldset rendering the computed blocks (counts/list excerpts via admin `display_*` methods over the model properties).
- `ArtworkAdmin`: expose `is_highlighted` and `views_count` in the form, changelist, and filters.

**Tests**: coverage for the new models, the Artwork fields, the Artist derived properties, and the admin additions.

**Migrations**: new `0003_...` — 3 `CreateModel` + 3 `AddField`, no data step.

## Capabilities

### New Capabilities

- `artist-social-links`: The `ArtistSocialLink` model — multiple typed social network links per artist (platform + URL), admin inline editing, and seed fixture.
- `artist-location`: The `Location` model with bilingual translations and its FK on `Artist` (many artists per location), plus base/seed fixtures and admin management.
- `artwork-discovery-flags`: The `Artwork.is_highlighted` and `Artwork.views_count` fields and their admin exposure (form, changelist, filter).
- `artist-derived-fields`: Reusable computed properties on `Artist` (techniques, available_artworks, new_additions, highlighted_artworks, most_viewed, curations) and the readonly admin "Resumen" fieldset that renders them.

### Modified Capabilities

- `artist-admin`: The Artist admin form/change view gains a `location` selector, the social links inline, and the readonly "Resumen" fieldset with computed counts.
- `artwork-admin`: The Artwork admin form, changelist, and filters gain the `is_highlighted` and `views_count` fields.

## Impact

- **Code**: `artworks/models.py`, `artworks/admin.py`, `artworks/tests.py`, new migration `artworks/migrations/0003_...`.
- **New files**: `artworks/fixtures/artworks/Location.json`, `artworks/fixtures/artworks/LocationTranslation.json`, `artworks/fixtures/artworks/seed/ArtistSocialLink.json`; updates to `seed/Artist.json`.
- **Data**: DB gains two new tables + three new columns; taxonomy/seed loading pattern (`base_loaddata`/`seed_loaddata`) is reused — no data migration needed.
- **Out of scope**: public API/serializers (future change, will reuse the model properties), view-tracking increments (no views exist yet), and "más vendidos" (deferred to the sales app).
