## 1. Filter implementations (`artworks/admin_filters.py`)

- [x] 1.1 Rewrite `HasRelatedFilter.queryset()` to use `Exists`/`OuterRef` subqueries instead of inner-join + `.distinct()` (import `Exists`, `OuterRef` from `django.db.models`).
- [x] 1.2 Rewrite `ArtistAvailableWorksFilter.queryset()` (in `artworks/admin.py`) to use an `Exists` subquery for both "with" and "without" lookups, dropping `.distinct()`.
- [x] 1.3 Rewrite `YearFilter.lookups()` to derive decades from `Min("year")`/`Max("year")` aggregates on the model instead of `get_queryset(...).values_list(...).distinct()`.

## 2. `ArtistAdmin` changelist counts (`artworks/admin.py`)

- [x] 2.1 Add `get_queryset()` to `ArtistAdmin` annotating `_artworks_count`, `_available_count`, `_techniques_count`, `_highlighted_count`, `_galleries_count` via `Count` with `filter=`/`distinct=True` (import `Count`, `Q`).
- [x] 2.2 Update `display_artworks_count` to return `obj._artworks_count` (remove the per-row `.filter().count()`).
- [x] 2.3 Update `display_available_count` to return `obj._available_count`.
- [x] 2.4 Update `display_techniques_count` to return `obj._techniques_count`.
- [x] 2.5 Update `display_highlighted_count` to return `obj._highlighted_count`.
- [x] 2.6 Update `display_galleries_count` to return `obj._galleries_count`.

## 3. `ArtworkAdmin` changelist cells (`artworks/admin.py`)

- [x] 3.1 Add `get_queryset()` to `ArtworkAdmin` prefetching `images`, `translations`, and `disciplines__translations`, `techniques__translations`, `themes__translations`, `formats__translations`, `scales__translations`.
- [x] 3.2 Rewrite `display_image` to select the primary (else first) image from `obj.images.all()` in Python.
- [x] 3.3 Rewrite `display_title` to select the ES (else first) translation from `obj.translations.all()` in Python.
- [x] 3.4 Rewrite `display_taxonomies` to iterate the 5 prefetched M2M relations and their prefetched translations in Python (ES-first name selection); replace `filter_horizontal` with `autocomplete_fields` on `ArtworkAdmin`.

## 4. Catalog admins shared translation mixin

- [x] 4.1 Create `TranslatableNameAdminMixin` in `project/admin_base.py` providing `get_queryset()` with `prefetch_related("translations")` and a `display_name` that selects the ES-first name from the cache in Python (`@admin.display(description="Nombre")`).
- [x] 4.2 Adopt the mixin in `DisciplineAdmin`, removing its inline `display_name`.
- [x] 4.3 Adopt the mixin in `TechniqueAdmin`, removing its inline `display_name`.
- [x] 4.4 Adopt the mixin in `ThemeAdmin`, removing its inline `display_name`.
- [x] 4.5 Adopt the mixin in `FormatAdmin`, removing its inline `display_name`.
- [x] 4.6 Adopt the mixin in `ScaleAdmin`, removing its inline `display_name`.
- [x] 4.7 Adopt the mixin in `LocationAdmin`, removing its inline `display_name`.
- [x] 4.8 Adopt the mixin in `GalleryAdmin`, removing its inline `display_name`.

## 5. Verification

- [x] 5.1 Run `python manage.py check` to confirm no import/syntax errors.
- [x] 5.2 Load the Artist, Artwork, and one catalog changelist and confirm query counts per page dropped to a constant (constant main query + fixed prefetch queries), with no per-row `.count()`/`.filter()` spikes, using Django Debug Toolbar or `assertNumQueries`-style checks.
- [x] 5.3 Manually confirm rendered values unchanged: Artist count columns, Artwork image/title/taxonomy cells, YearFilter decade options, and "con/sin obras" filter behavior.
- [x] 5.4 Open an Artwork change form and confirm the 5 taxonomy fields render as autocomplete widgets with search working.

## 6. Test-environment staticfiles fix

- [x] 6.1 Add a project-level `conftest.py` fixture that overrides `STORAGES["staticfiles"]` to `StaticFilesStorage` during pytest runs (the whitenoise manifest backend fails admin template renders under pytest because `staticfiles.json` is only built by `collectstatic`).
- [x] 6.2 Run the full test suite via pytest and confirm all previously failing admin view/render tests pass (baseline: 42 failures; target: 0).