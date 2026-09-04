# admin-list-performance

## Purpose
To define the performance requirements for the Django Admin changelists and
filters, ensuring Artist and Artwork changelists render without per-row queries,
translated names and counts are computed in the main query or from prefetched
caches, and admin views remain testable during Django tests via IS_TESTING fallback.

## Requirements

### Requirement: Artist changelist counts rendered in main query
The system SHALL compute all five count columns shown on the Artist changelist
(`display_artworks_count`, `display_available_count`, `display_techniques_count`,
`display_highlighted_count`, `display_galleries_count`) as SQL annotations in
`ArtistAdmin.get_queryset()` so that rendering a page does not issue a separate
COUNT query per row.

#### Scenario: Artist changelist renders counts with constant queries
- **WHEN** an administrator opens the Artist changelist with 50 rows per page
- **THEN** all five count columns for every row SHALL be populated from
  annotations attached to the main query, and no additional `.count()` query
  SHALL be executed per displayed artist.

#### Scenario: Annotated artworks count respects active filter
- **WHEN** an artist has artworks that are both active and inactive
- **THEN** the artworks count SHALL equal the number of active artworks only.

#### Scenario: Annotated available count respects status
- **WHEN** an artist has artworks with mixed statuses
- **THEN** the available count SHALL equal the number of artworks with status
  `available` and `is_active=True`.

#### Scenario: Techniques count de-duplicates shared techniques
- **WHEN** an artist has two artworks sharing the same technique
- **THEN** the techniques count SHALL count that technique once.

#### Scenario: Galleries count de-duplicates galleries
- **WHEN** multiple artworks of an artist are exhibited in the same active gallery
- **THEN** the galleries count SHALL count that gallery once.

### Requirement: Artwork changelist cells render from prefetched relations
The system SHALL prefetch `images`, `translations`, and the five taxonomy M2M
relations with their translations in `ArtworkAdmin.get_queryset()`, and SHALL
select the displayed values from that cache in Python, not via related-manager
`.filter(...)` queries.

#### Scenario: Artwork primary image comes from prefetched images
- **WHEN** an administrator opens the Artwork changelist
- **THEN** the image cell SHALL render the primary image (or first image) using
  the prefetched `images` cache without issuing a per-row query.

#### Scenario: Artwork title prefers the Spanish translation
- **WHEN** an artwork has both Spanish and English translations
- **THEN** the title cell SHALL render the Spanish title from the prefetched
  translations cache.

#### Scenario: Taxonomy column uses prefetched translations
- **WHEN** an artwork assigns disciplines, techniques, themes, formats, and scales
- **THEN** the classification cell SHALL render the Spanish names of those
  taxonomies using prefetched `*__translations` caches without per-row queries.

### Requirement: YearFilter builds decade options from aggregate bounds
The system SHALL compute `YearFilter` decade options from the minimum and
maximum `year` values in the artwork table (via `Min`/`Max`), not by scanning
every distinct year in the full queryset.

#### Scenario: Decades are derived from min and max year
- **WHEN** an administrator opens the Artwork changelist
- **THEN** the year filter SHALL offer decade ranges spanning from the decade of
  the minimum artwork year to the decade of the maximum artwork year.

#### Scenario: Empty artwork table yields no decade options
- **WHEN** the artwork table contains no rows
- **THEN** the year filter SHALL render no decade options.

#### Scenario: Decade selection filters artworks
- **WHEN** an administrator selects a decade option
- **THEN** the changelist SHALL show only artworks whose `year` falls within
  that decade.

### Requirement: Artwork taxonomy editing uses autocomplete
The system SHALL replace `filter_horizontal` with `autocomplete_fields` for
`disciplines`, `techniques`, `themes`, `formats`, and `scales` on
`ArtworkAdmin`, loading related records on demand via search instead of all at
once.

#### Scenario: Taxonomy fields load on demand
- **WHEN** an administrator opens the Artwork change form
- **THEN** the five taxonomy fields SHALL render as autocomplete widgets that
  do not preload the full option list.

#### Scenario: Autocomplete searches translated names
- **WHEN** an administrator types a name in a taxonomy autocomplete
- **THEN** matching records SHALL be returned by slug or by translated name.

### Requirement: Catalog admins render translated names without N+1 queries
The system SHALL provide a shared mixin for the catalog admins (Discipline,
Technique, Theme, Format, Scale, Location, Gallery) that prefetches
`translations` in the changelist queryset and renders the ES-first name from
the cache in Python.

#### Scenario: Catalog changelist renders names from prefetch cache
- **WHEN** an administrator opens any catalog changelist
- **THEN** every row's name cell SHALL render from the prefetched
  `translations` cache without a per-row query.

#### Scenario: Catalog name prefers Spanish, falls back to first translation
- **WHEN** an object has a Spanish translation
- **THEN** the name SHALL render the Spanish translation; when only a non-Spanish
  translation exists, the name SHALL render that translation.

### Requirement: Related-existence filters use EXISTS subqueries
The system SHALL implement `HasRelatedFilter` and `ArtistAvailableWorksFilter`
filtering with `Exists`/`OuterRef` subqueries instead of inner joins plus
`.distinct()`.

#### Scenario: Records with related records
- **WHEN** an administrator selects a "with" lookup
- **THEN** the changelist SHALL include only records having at least one related
  record, without duplicates.

#### Scenario: Records without related records
- **WHEN** an administrator selects a "without" lookup
- **THEN** the changelist SHALL include only records having no related record.

#### Scenario: Ordering is preserved when filtering
- **WHEN** an administrator applies any related-existence filter
- **THEN** the changelist SHALL preserve the default ordering and pagination of
  the underlying model.

### Requirement: Admin views render during Django tests without a staticfiles manifest
The system SHALL use Django's `IS_TESTING` (`project/settings.py:88`) to select `django.contrib.staticfiles.storage.StaticFilesStorage` for the `staticfiles` backend during `python manage.py test` (`project/settings.py:203-214`), so admin changelist, change, and add views render without requiring a `staticfiles.json` manifest built by `collectstatic`. No pytest fixture (`conftest.py`) SHALL be required. Outside tests the configured Whitenoise manifest backend SHALL remain unchanged.

#### Scenario: Django test run renders admin views
- **WHEN** the test suite runs via `python manage.py test`
- **THEN** admin changelist, change, and add views SHALL render successfully without a "Missing staticfiles manifest entry" error.

#### Scenario: Production staticfiles behavior unchanged
- **WHEN** the application runs outside tests
- **THEN** the configured `whitenoise.storage.CompressedManifestStaticFilesStorage` backend SHALL remain unchanged and SHALL still require `collectstatic` to build `staticfiles.json`.
