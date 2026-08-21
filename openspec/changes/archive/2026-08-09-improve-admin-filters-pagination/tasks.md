## 1. Reusable filter classes

- [x] 1.1 Create `artworks/admin_filters.py` with the generic `HasRelatedFilter(SimpleListFilter)` class that filters on a relation's presence (lookups: all / "with" / "without") using `{related}__isnull`.
- [x] 1.2 Create the `YearFilter(SimpleListFilter)` class in `artworks/admin_filters.py` that builds decade lookups from distinct `year` values and filters with `year__gte`/`year__lt`.

## 2. Artwork admin

- [x] 2.1 Add `artist` to `ArtworkAdmin.list_filter` using `RelatedOnlyFieldListFilter`.
- [x] 2.2 Add a `gallery` filter to `ArtworkAdmin.list_filter` via `gallery_links__gallery` using `RelatedOnlyFieldListFilter`.
- [x] 2.3 Add `YearFilter` to `ArtworkAdmin.list_filter` for the `year` field.
- [x] 2.4 Add `created_at` to `ArtworkAdmin.list_filter`.
- [x] 2.5 Change the five taxonomy filters to `RelatedOnlyFieldListFilter`: `disciplines`, `techniques`, `themes`, `formats`, `scales`.
- [x] 2.6 Set `list_per_page = 25` on `ArtworkAdmin`.

## 3. Artist admin

- [x] 3.1 Add `location` to `ArtistAdmin.list_filter` using `RelatedOnlyFieldListFilter`.
- [x] 3.2 Add `created_at` to `ArtistAdmin.list_filter`.
- [x] 3.3 Add a `HasRelatedFilter` for `artworks` ("obras") to `ArtistAdmin.list_filter`.
- [x] 3.4 Add a custom lookup-based filter to `ArtistAdmin.list_filter` for artists with at least one active artwork with status `available` ("con obras disponibles").
- [x] 3.5 Set `list_per_page = 50` on `ArtistAdmin`.

## 4. Gallery and ArtCurator admins

- [x] 4.1 Add `curator` to `GalleryAdmin.list_filter` using `RelatedOnlyFieldListFilter`.
- [x] 4.2 Add a `HasRelatedFilter` for `artwork_links` ("obras") to `GalleryAdmin.list_filter`.
- [x] 4.3 Add a `HasRelatedFilter` for `curated_galleries` ("galerías") to `ArtCuratorAdmin.list_filter`.

## 5. Taxonomy admins

- [x] 5.1 Add a `HasRelatedFilter` for `artworks` ("obras", in-use) to each of `DisciplineAdmin`, `TechniqueAdmin`, `ThemeAdmin`, `FormatAdmin`, `ScaleAdmin`, and `LocationAdmin` list filters.

## 6. Index and migration

- [x] 6.1 Add `db_index=True` to `TimeStampedModel.created_at` in `core/models.py`.
- [x] 6.2 Generate migrations with `python manage.py makemigrations`.

## 7. Tests and verification

- [x] 7.1 Update `artworks/tests.py` admin filter assertions to reflect the new `list_filter` contents (keep existing `assertIn` checks valid).
- [x] 7.2 Run `python manage.py check` to validate admin configuration.
- [x] 7.3 Run the test suite (`python manage.py test`) and fix any failures.
