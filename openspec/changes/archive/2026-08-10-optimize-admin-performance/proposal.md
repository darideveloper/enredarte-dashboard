## Why

The Django admin list views for `Artwork` and `Artist` fire hundreds of database
queries per page load due to per-row `.count()` calls, translation lookups via
`.filter(...).first()` on related managers, and inefficient filter implementations.
The `YearFilter` scans every artwork row on every page load just to build decade
options, `filter_horizontal` renders all taxonomy records into the DOM on any
artwork edit form, and catalog admins repeat an N+1 translation pattern across 7
models.

## What Changes

- Replace per-row `.count()` calls in `ArtistAdmin.list_display` with SQL
  annotations computed in `get_queryset()`.
- Replace per-row related lookups in `ArtworkAdmin.list_display`
  (`display_image`, `display_title`, `display_taxonomies`) with
  `prefetch_related` + Python-side filtering, so list pages stop hitting the DB
  once per cell.
- Rewrite `YearFilter.lookups()` to derive decades from `Min`/`Max` aggregates
  instead of a full-table scan.
- Replace `filter_horizontal` in `ArtworkAdmin` with `autocomplete_fields` for
  the 5 taxonomy M2M fields.
- Eliminate the N+1 `display_name` translation pattern in catalog admins
  (Discipline, Technique, Theme, Format, Scale, Location, Gallery) via
  `prefetch_related("translations")` + Python-side ES lookup.
- Rewrite `HasRelatedFilter.queryset()` to use `Exists`/`OuterRef` subqueries
  instead of `.distinct()` on joined querysets.

## Capabilities

### New Capabilities
- `admin-list-performance`: Query-count optimizations for Django admin list
  views and filters across the artworks app (annotations, prefetching,
  Python-side related lookups, `Min`/`Max`-based filters, subquery-based
  existence filters).

### Modified Capabilities
<!-- None: existing specs cover admin behavior/fields, not performance. This is
     purely additive query optimization with no spec-level behavior change. -->

## Impact

- `artworks/admin.py` — `ArtistAdmin`, `ArtworkAdmin`, 7 catalog admins
  (`get_queryset` overrides, `display_*` methods, `autocomplete_fields`).
- `artworks/admin_filters.py` — `HasRelatedFilter.queryset()`, `YearFilter.lookups()`.
- `conftest.py` — new project-level fixture overriding the staticfiles backend
  to `StaticFilesStorage` under pytest (fixes 42 test failures caused by the
  whitenoise manifest storage).
- No model schema changes (`artworks/models.py` is untouched), no migrations,
  no new dependencies.