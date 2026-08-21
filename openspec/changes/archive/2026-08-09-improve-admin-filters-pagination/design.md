## Context

The Django admin (Unfold) in this project manages an art catalog. Every custom model admin currently exposes only `["is_active"]` as a `list_filter`, except `Artwork` which filters by `status`, `is_active`, `is_highlighted`, and five M2M taxonomies. Changelists use Django's default `list_per_page = 100`. The `Artwork` and `Artist` list views render expensive per-row lookups (primary image, localized title, 5 M2M taxonomy summaries with their translations, multiple COUNT subqueries) with no `get_queryset` prefetching. No custom `SimpleListFilter` exists anywhere in the codebase today.

Constraints discovered during exploration:
- `Artwork.year` is an `IntegerField` — Django has no built-in filter for it.
- `created_at` (`TimeStampedModel`) is `auto_now_add` and not indexed; Django's `DateFieldListFilter` needs an index for fast dropdown aggregation on large tables.
- The five taxonomy M2M filters currently render ALL taxonomy rows; many taxonomies are unused.
- Reverse relations used for "has X" filters: `Artist.artworks`, `Gallery.artwork_links`, `ArtCurator.curated_galleries`, `Artwork.gallery_links` (through `ArtworkGallery`).
- `tests.py` asserts on `list_filter` contents (e.g., `is_highlighted in artwork_admin.list_filter`).

## Goals / Non-Goals

**Goals:**
- Add the high-value filters recommended in exploration: `artist`, `gallery`, and year/decade on `Artwork`; `location`, `created_at`, "has artworks", "with available works" on `Artist`; `curator` and "has artworks" on `Gallery`; "has galleries" on `ArtCurator`; "in use" on all taxonomies.
- Add `created_at` date filter on `Artwork` and `Artist`.
- Reduce changelist query load by lowering `list_per_page` on the expensive models (Artwork 25, Artist 50) and shrinking taxonomy filter dropdowns via `RelatedOnlyFieldListFilter`.
- Keep the implementation minimal and reusable: the generic `HasRelatedFilter` and `YearFilter` classes cover the presence and year cases; the "with available works" filter is a distinct small lookup-based filter.

**Non-Goals:**
- Rewriting `list_display` methods or adding `get_queryset` prefetch/annotate optimizations — that is a separate performance change and out of scope here.
- Changing the changeform (edit page) behavior, `filter_horizontal` widgets, or inline configs.
- Filter changes on `User`, `Group`, or `TokenProxy`.
- Any frontend/public-site changes.

## Decisions

### 1. One generic `HasRelatedFilter` instead of per-model custom filters
A single `SimpleListFilter` subclass takes the related field name and a human label, and exposes `Todos / Con <label> / Sin <label>`. Instantiated per admin via a small helper, e.g. `HasRelatedFilter("artworks", "obras")`.

- **Why**: The "is referenced / has children" pattern repeats across 9+ models. One class is ~30 lines; per-model filters would duplicate it nine times.
- **Alternative considered**: a boolean "Solo con X" dropdown vs. three options. Chose three options (with/without/all) since "without" catches incomplete profiles and unused taxonomies — the actual data-hygiene use case.
- **Implementation**: `lookup` values like `"with"` / `"without"` mapping to `{f"{related}__isnull": False}` and `{f"{related}__isnull": True}`.
- **Note**: `HasRelatedFilter` does NOT cover the "with available works" filter on Artist, which needs `artworks__is_active=True, artworks__status="available"`. That is a separate lookup-based `SimpleListFilter` (implemented as its own class), not the `__isnull` pattern.

### 2. `YearFilter` with decade buckets for `Artwork.year`
A `SimpleListFilter` whose `lookups` are computed from distinct years mapped to decade ranges (e.g., `1980-1989`).

- **Why**: art catalogs are naturally browsed by era; exact-year dropdowns over many distinct years are noisy.
- **Alternative considered**: exact-year dropdown — rejected as too long; min/max range UI — rejected as over-engineered (two lookup parameters, custom templates). Decades are one lookup per decade, backend-only.
- **Implementation**: `lookups` returns `(decade_start, "1980–1989")` pairs; `queryset` filters `year__gte=start, year__lt=start+10`. Distinct years fetched once per request via `values_list("year", flat=True).distinct()`.

### 3. `RelatedOnlyFieldListFilter` for the five taxonomy M2M filters
Swap the default M2M filter for `RelatedOnlyFieldListFilter` so dropdowns only show taxonomies actually referenced by at least one artwork. Apply the same filter to the `artist` FK on Artwork, `curator` FK on Gallery, and `location` FK on Artist so those dropdowns also only list records actually in use (avoids unwieldy dropdowns as the catalog grows).

- **Why**: smaller dropdowns, less noise, and a subquery filter that's cheap on the M2M through tables. Without it, FK filters list every artist/curator/location even those unused by the filtered model.
- **Alternative considered**: custom `AllValuesFieldListFilter` — rejected, it doesn't dedupe to "in use".

### 4. `gallery` filter on Artwork via the through relation
Filter artworks by gallery using `gallery_links__gallery` (through `ArtworkGallery`, which has a composite unique index on `(artwork, gallery)`).

- **Why**: natural "what's in this gallery" navigation; the through table is indexed so the join is cheap.
- **Alternative considered**: listing `ArtworkGallery` objects — rejected, that's a hidden admin model, not the artwork list.

### 5. `created_at` date filter with an index
Add `db_index=True` to `created_at` in `TimeStampedModel` (or a targeted index on `Artwork.created_at` via a migration) and include `created_at` in `ArtworkAdmin.list_filter` and `ArtistAdmin.list_filter`.

- **Why**: Django's date filter aggregates `DISTINCT DATE(created_at)` for its dropdown; unindexed that scan degrades past ~10K rows. The index is a one-line migration cost.
- **Decision**: index the base abstract field `TimeStampedModel.created_at` so all timestamped models benefit (Artist recently-onboarded filter is included in this change).

### 6. Pagination: Artwork 25, Artist 50; rest default 100
Set `list_per_page` only where row cost justifies it.

- **Why**: `ArtworkAdmin` rows each cost ~12+ queries (image, translation, 5 M2M + their translations); `ArtistAdmin` rows cost ~8 queries (5 COUNT subqueries + translation). Halving/quartering rows cuts total query count proportionally without touching query efficiency.
- **Alternative considered**: leaving defaults and only optimizing queries — rejected as out of scope (Non-Goals), pagination is a config-only mitigation.

### 7. New module `artworks/admin_filters.py` for reusable filters
Place `HasRelatedFilter` and `YearFilter` in a dedicated module imported by `artworks/admin.py`, keeping the already-large admin file manageable.

- **Why**: separation of concerns; avoids bloating `admin.py` (currently 750 lines) with generic filter classes.

## Risks / Trade-offs

- [YearFilter computes distinct years per request] → The query is a single `SELECT DISTINCT year` on a 4-byte integer column; milliseconds even at 100K rows. Acceptable.
- [`created_at` index adds write overhead] → One integer timestamp index; negligible on catalog write rates. Reversible via migration rollback.
- [New filters change `list_filter` content, breaking existing tests that assert on it] → Update `artworks/tests.py` assertions as part of this change; tests only check membership (`assertIn`), so additions don't break, removals do — none are removed.
- [`RelatedOnlyFieldListFilter` on taxonomies could hide options a user wants] → Only unused taxonomies are hidden; creating an artwork with a new taxonomy makes it reappear immediately.
- [Decade buckets may not fit catalogs spanning few years] → Buckets are derived from actual distinct years; a narrow catalog yields few, precise buckets.

## Migration Plan

1. Add `db_index=True` to `TimeStampedModel.created_at`.
2. Generate migration: `python manage.py makemigrations artworks core`.
3. Deploy migration + code together.
4. Rollback: revert commit and run `python manage.py migrate <app> <previous>` — no data loss; filters and pagination are admin-only UI.
