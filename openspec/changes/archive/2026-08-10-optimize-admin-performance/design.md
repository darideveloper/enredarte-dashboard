## Context

The Django admin for the `artworks` app is the primary data-entry tool. Profiling
the changelist views (see `artworks/admin.py`) reveals hundreds of queries per
page load because `list_display` methods re-query the DB once per rendered row:

- `ArtistAdmin` shows 5 count columns; each `display_*_count` calls `.count()`
  on a related queryset, so a 50-row page issues ~250 extra COUNT queries.
- `ArtworkAdmin` shows `display_image`, `display_title` and `display_taxonomies`
  which call `.filter(...).first()` / `.all()` on related managers (images,
  translations, and 5 M2M taxonomies + their translations), adding tens of
  queries per row. With `list_per_page = 25`, a single page can issue
  ~500–1500 queries.
- `YearFilter.lookups()` runs `model_admin.get_queryset(request).values_list(...).distinct()`
  on every changelist load — a full scan of the `artwork` table to build decade
  options, even when the filter is unused.
- `ArtworkAdmin.filter_horizontal` renders every taxonomy record into the edit
  form DOM, leaving the change form sluggish as catalogs grow.
- The 7 catalog admins (Discipline, Technique, Theme, Format, Scale, Location,
  Gallery) repeat an identical N+1 `display_name` which looks up the ES
  translation via a related-manager `.filter(...)` per row.
- `HasRelatedFilter.queryset()` and `ArtistAvailableWorksFilter` use inner-join +
  `.distinct()` to test related-record existence, forcing the DB to materialize
  and deduplicate joined rows.

All registered models: User, Group, TokenProxy (fine — no N+1), Artist,
ArtCurator, Discipline, Technique, Theme, Format, Scale, Location, Gallery,
Artwork. Only the artworks-app models need optimization.

## Goals / Non-Goals

**Goals:**

- Cut changelist query counts from ~O(rows × related-lookups) to a constant
  number of queries per page (1 main query + N prefetch queries).
- Keep rendered list content identical: same columns, same values, same filters.
- Fix the shared filter implementations once so all admins using them benefit.
- Keep the change form for Artwork lightweight via `autocomplete_fields`.

**Non-Goals:**

- No model schema changes, no migrations, no new dependencies.
- No caching layer (memcached/Redis) — query-count elimination is sufficient
  and simpler than cache invalidation.
- No pagination/UI changes beyond what already exists.
- No changes to User/Group/TokenProxy admins (already optimal).
- No change to stored data or API responses; optimized properties on the
  **model** (e.g. `available_artworks`) are left untouched since the admin
  display methods will read annotations/prefetch instead of those querysets.

## Decisions

### 1. Artist counts → SQL annotations in `get_queryset()`
Use `django.db.models.Count` with a `filter=` kwarg (Django ≥ 2.0) and
`distinct=True` where joins can duplicate rows, computed in ONE query:

```python
def get_queryset(self, request):
    return (
        super().get_queryset(request)
        .annotate(
            _artworks_count=Count("artworks", filter=Q(artworks__is_active=True), distinct=True),
            _available_count=Count(
                "artworks",
                filter=Q(artworks__is_active=True, artworks__status=ArtworkStatus.AVAILABLE),
                distinct=True,
            ),
            _techniques_count=Count("artworks__techniques", distinct=True),
            _highlighted_count=Count(
                "artworks",
                filter=Q(artworks__is_active=True, artworks__is_highlighted=True),
                distinct=True,
            ),
            _galleries_count=Count(
                "artworks__gallery_links__gallery",
                filter=Q(artworks__gallery_links__gallery__is_active=True),
                distinct=True,
            ),
        )
    )
```

Each `display_*_count` then reads its annotated attribute instead of calling
`.count()`. **`distinct=True` is required on ALL five counts, not just the
techniques/galleries ones**: the `artworks__techniques` and
`artworks__gallery_links__gallery` joins fan out rows, so a plain
`COUNT(artwork.id)` would over-count artworks (an artist with 2 artworks × 3
techniques each would join 6 `artwork` rows). `COUNT(DISTINCT artwork.id)` keeps
each artwork counted once regardless of the join expansion.

*Alternative considered:* `prefetch_related` + `len()` — rejected because
prefetching all artworks (to then count in Python) transfers far more rows to
the ORM than a COUNT in SQL, and the annotation runs entirely in the DB.
*Alternative considered:* keep `.count()` but `select_related`/`prefetch` —
rejected: `.count()` always issues a query and bypasses the prefetch cache.

### 2. Artwork list cells → `prefetch_related` + Python-side selection
Add to `ArtworkAdmin.get_queryset()`:

```python
.prefetch_related("images")
.prefetch_related("translations")
.prefetch_related("disciplines__translations")
.prefetch_related("techniques__translations")
.prefetch_related("themes__translations")
.prefetch_related("formats__translations")
.prefetch_related("scales__translations")
```

Rewrite the three display methods to consume the cache instead of issuing
manager queries:

- `display_image`: iterate `obj.images.all()` in Python, pick
  `is_primary` else first.
- `display_title`: iterate `obj.translations.all()` in Python, pick `language ==
  "es"` else first.
- `display_taxonomies`: for each of the 5 M2M names iterate `item.translations.all()`
  (cached via `__translations` prefetch) and select the ES name in Python.

Key subtlety: a related manager's `.filter(language="es").first()` does **not**
use the prefetch cache — it builds and executes a new query. Only iterating the
prefetched `.all()` list avoids the DB. The helper `_translated_name(holder)`
already exists on `ArtistAdmin`; Artwork needs an analogous local helper.

*Alternative considered:* `Prefetch(..., to_attr=...)` with an ordered queryset
to pick primary/first — rejected: plain prefetch + a Python `next(...)` is less
code and version-proof.

### 3. `YearFilter.lookups()` → derive decades from `Min`/`Max`
Replace the full `get_queryset(...).values_list("year", ...)` scan with two
aggregate reads:

```python
stats = model_admin.model.objects.aggregate(min_year=Min("year"), max_year=Max("year"))
if stats["min_year"] is None:
    return []
```

Build decade tuples from `min_year // 10 * 10` to `max_year // 10 * 10` stepping
by 10. This turns an O(N) full-row scan (plus `DISTINCT` + sort) into a
two-scalar aggregate read returning min/max years.

*Trade-off:* empty decades between min and max now appear as options (e.g.
1980–1989 listed even if no artwork from the 80s). Acceptable for a year filter;
keeps the filter list stable as data changes. Alternative — a fixed decade list
constant — rejected: it would need manual maintenance as the catalog grows.

### 4. Artwork edit form → `autocomplete_fields` instead of `filter_horizontal`
Delete `filter_horizontal` and set:

```python
autocomplete_fields = ["disciplines", "techniques", "themes", "formats", "scales"]
```

Each taxonomy admin already declares `search_fields` (`["slug", "translations__name"]`),
so autocomplete works out of the box. The form no longer loads all taxonomy
options into the DOM or issues one big query per field.

*Alternative considered:* `filter_vertical` — rejected, still loads all options.
`raw_id_fields` — rejected, poor UX for M2M compared to autocomplete.

### 5. Catalog admins → shared `TranslatableNameAdminMixin`
The 7 catalog admins duplicate identical `get_queryset` + `display_name` logic.
Extract one mixin in **`project/admin_base.py`** next to `ModelAdminUnfoldBase`
(already imported by every artworks admin) that:

- overrides `get_queryset` to `prefetch_related("translations")`;
- provides `display_name` that iterates `obj.translations.all()` in Python
  (ES-first, else first, else `"-"`), keeping the existing `@admin.display
  (description="Nombre")` label.

`ArtistAdmin`, `ArtCuratorAdmin` and `ArtworkAdmin` already use
`display_name`/`display_title` with `name`/translations of their own shape, so
they are NOT migrated to the mixin — it only covers the 7 `TranslatableName`
catalog models. Each catalog admin swaps its inline `display_name` for the
mixin version.

*Alternative considered:* annotate the ES name via `Subquery`/`Coalesce` per
admin — rejected: more SQL complexity for 7 small tables; prefetch + Python is
readable and fast enough at catalog scale (<200 rows).

### 6. Existence filters → `Exists` subquery, drop `.distinct()`
Rewrite `HasRelatedFilter.queryset()` and `ArtistAvailableWorksFilter` to use
`Exists(OuterRef(...))`:

```python
def queryset(self, request, queryset):
    def has():
        lookup = {f"{self.related}__isnull": False}
        return queryset.model.objects.filter(pk=OuterRef("pk"), **lookup)

    if self.value() == "with":
        return queryset.filter(Exists(has()))
    if self.value() == "without":
        return queryset.filter(~Exists(has()))
    return queryset
```

`Exists` becomes `WHERE EXISTS (SELECT 1 ...)` — the planner halts at the first
match, no row materialization or dedup, so the `.distinct()` disappears. The
`without` case is now a correct NOT EXISTS (previous `exclude(...)` over a join
had multi-valued-subquery pitfalls). Note: use `queryset.filter(Exists(...))`
directly — wrapping the subquery in `.alias(_h=...).filter(_h=True)` does NOT
emit the WHERE clause on Django 5.2.

`ArtistAvailableWorksFilter.queryset()` gets the same treatment with its own
two-condition lookup.

### 7. Test-environment staticfiles backend
`project.settings` selects the staticfiles backend from `IS_TESTING`, which is
only `True` under `manage.py test` (`sys.argv[1] == "test"`). Under pytest the
whitenoise `CompressedManifestStaticFilesStorage` is chosen, so any admin
template render fails with `ValueError: Missing staticfiles manifest entry` for
`favicon.png` (the manifest is only built by `collectstatic`). This produced 42
pre-existing test failures on the baseline.

Add a project-level `conftest.py` with an autouse fixture that replaces
`STORAGES["staticfiles"]` with `django.contrib.staticfiles.storage.StaticFilesStorage`
for every pytest test, leaving the configured production backend untouched
outside tests.

*Alternative considered:* broadening `IS_TESTING` in settings.py to detect
pytest (e.g. `os.environ.get("PYTEST_CURRENT_TEST")`) — rejected: `settings.py`
is read once at process start, before any test marker is set, so env detection
is unreliable and it couples test concerns into production config. The
`conftest.py` fixture is explicit, self-documenting, and scoped to tests only.

## Risks / Trade-offs

- **Annotation semantics drift from the model properties** → The annotated
  counts must match `display_artworks_count` semantics exactly (filter `is_active`,
  status, etc.). Mitigation: each annotation mirrors the exact filter used by the
  current property; a regression would only change the displayed number, caught
  by a single manual check of one artist whose counts are known.

- **`prefetch_related` memory spike on large pages** → Prefetching images +
  translations + 5 taxonomies for 25 artworks is bounded (a few hundred rows).
  If artwork counts grow ~100k+, revisit with `Prefetch(..., queryset=...limit)`
  or drop `display_taxonomies` from the list. Not a concern at current scale.

- **Autocomplete changes UX** → Editors go from "click all options" to
  "type to search". Discovery of available taxonomies is slightly worse.
  Mitigation: `search_fields` already matches names in both languages; the
  filter sidebar still lists all taxonomies.

- **Empty decades listed by YearFilter** → Cosmetic; options stay stable and
  always valid. If a decade has no results the query just returns empty.

- **`YearFilter` still runs Min/Max on an unindexed `year` column** → Current
  `year` has no DB index, so MIN/MAX scans the table once — still O(N) but
  returns 2 scalars with no DISTINCT/sort/data transfer, far cheaper than today.
  Adding an index is a migration and out of scope (Non-Goal); revisit if the
  artwork table grows large.

## Migration Plan

1. Implement in dependency order: `project/admin_base.py` mixin →
   `artworks/admin_filters.py` (YearFilter + HasRelatedFilter + ArtistAvailableWorksFilter)
   → `artworks/admin.py` (Artist annotations, Artwork prefetch/autocomplete,
   catalog mixin adoption).
2. Verify each changelist with Django Debug Toolbar or
   `django.db.connection.queries`/`assertNumQueries` before/after to confirm
   query-count reduction.
3. Rollback: revert the admin changes (pure code, no schema). No data migration,
   no irreversible state — safe to deploy incrementally.

## Open Questions

- None.