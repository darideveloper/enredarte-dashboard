## Why

The Django admin list views are hard to navigate and get slow as the catalog grows. Most models only offer an `is_active` filter — there is no way to browse artworks by artist, gallery, or year, artists by location, or galleries by curator. Meanwhile the changelist pages render expensive per-row queries (N+1 on images, translations, and the five taxonomy axes) with Django's default 100 rows per page, so large models like Artwork and Artist degrade noticeably.

## What Changes

- Add a reusable `HasRelatedFilter` `SimpleListFilter` class that filters records by whether they reference related objects (e.g., artists with/without artworks, taxonomies in use/unused).
- Add a reusable `YearFilter` `SimpleListFilter` for `Artwork.year`, exposing decade buckets.
- **Artwork admin** (`ArtworkAdmin`):
  - Add filters: `artist`, `gallery` (via `ArtworkGallery`), and year/decade.
  - Switch the five taxonomy filters (`disciplines`, `techniques`, `themes`, `formats`, `scales`) to `RelatedOnlyFieldListFilter`.
  - Set `list_per_page` to 25.
  - Add `created_at` date filter.
- **Artist admin** (`ArtistAdmin`):
  - Add filters: `location`, `created_at` ("recently onboarded"), "has artworks", and "with available works".
  - Set `list_per_page` to 50.
- **Gallery admin** (`GalleryAdmin`):
  - Add filters: `curator` and "has artworks".
- **ArtCurator admin** (`ArtCuratorAdmin`):
  - Add "has galleries" filter.
- **Taxonomy admins** (`DisciplineAdmin`, `TechniqueAdmin`, `ThemeAdmin`, `FormatAdmin`, `ScaleAdmin`, `LocationAdmin`):
  - Add "in use" filter (references an artwork).
- **User/Group/Token admins**: unchanged (already adequate).
- Add a database index on the abstract `TimeStampedModel.created_at` field (inherited by all artworks models) to keep the new date filters fast (migration).
- Apply `RelatedOnlyFieldListFilter` to the `artist` (Artwork), `curator` (Gallery), and `location` (Artist) FK filters so dropdowns only list records actually in use.

## Capabilities

### New Capabilities
- `admin-filters-pagination`: Cross-cutting admin capabilities for reusable list filters (`HasRelatedFilter`, `YearFilter`) and per-model pagination tuning across the artworks admin.

### Modified Capabilities
- `artwork-admin`: Adds `artist`, `gallery`, and year/decade filters; switches taxonomy filters to `RelatedOnlyFieldListFilter`; adds `created_at` filter; reduces `list_per_page` to 25.
- `artist-admin`: Adds `location`, `created_at`, "has artworks", and "with available works" filters; reduces `list_per_page` to 50.
- `gallery-admin`: Adds `curator` and "has artworks" filters.
- `art-curator-admin`: Adds "has galleries" filter.

## Impact

- **Files**: `artworks/admin.py` (primary), `core/models.py` or `artworks/models.py` (index on `created_at`), new migration in `artworks/migrations/`, reusable filter classes (new module, e.g., `artworks/admin_filters.py`).
- **Tests**: `artworks/tests.py` asserts on `list_filter` contents (`test_artwork_admin` asserts `is_highlighted` in `list_filter`); tests asserting filter lists or page behavior will need updates.
- **Performance**: fewer rows per page cuts changelist query count (~75% for Artwork, ~50% for Artist); `RelatedOnlyFieldListFilter` keeps filter dropdowns small; date filter requires indexed `created_at`.
- **No public-facing API or frontend changes**; admin-only change.
- **No breaking changes**.
