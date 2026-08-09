# Admin Filters and Pagination Specification

## ADDED Requirements

### Requirement: Reusable HasRelatedFilter
The system SHALL provide a reusable `SimpleListFilter` class (`HasRelatedFilter`) that filters a changelist on whether records reference a given related object via a provided reverse/filter relation name, offering "all", "with", and "without" lookups.

#### Scenario: Filtering by presence of related records
- **WHEN** an administrator opens a changelist configured with `HasRelatedFilter` for a relation
- **THEN** the filter sidebar SHALL show options to view all records, only records that have related records ("with"), or only records without them ("without").

#### Scenario: Filtering records without related records
- **WHEN** an administrator selects the "without" lookup
- **THEN** the queryset SHALL only include records where the related relation is empty (e.g., artists with no artworks, taxonomies not used by any artwork).

#### Scenario: Filtering records with related records
- **WHEN** an administrator selects the "with" lookup
- **THEN** the queryset SHALL only include records where the related relation is non-empty.

### Requirement: Reusable YearFilter
The system SHALL provide a `SimpleListFilter` class (`YearFilter`) for filtering integer `year` fields by decade buckets derived from the distinct years present in the queryset.

#### Scenario: Filtering by decade
- **WHEN** an administrator opens an Artwork changelist and the year filter
- **THEN** the options SHALL be decade ranges (e.g., `1980-1989`) computed from the distinct `year` values, and selecting one SHALL return only artworks whose year falls within that decade.

### Requirement: Indexed created_at timestamp
The system SHALL add a database index on `TimeStampedModel.created_at` so date-range list filters over the timestamp are efficient.

#### Scenario: Applying a created_at date filter
- **WHEN** an administrator uses a date-range filter on `created_at`
- **THEN** the database index is used and the query completes without a full table scan.

### Requirement: Pagination tuning per model
The system SHALL set `list_per_page` to 25 on `ArtworkAdmin` and 50 on `ArtistAdmin`, keeping the Django default (100) on all other registered admin models.

#### Scenario: Browsing the Artwork changelist
- **WHEN** an administrator opens the Artwork changelist
- **THEN** at most 25 artworks SHALL be rendered per page.

#### Scenario: Browsing the Artist changelist
- **WHEN** an administrator opens the Artist changelist
- **THEN** at most 50 artists SHALL be rendered per page.

### Requirement: In-use filter on taxonomy admins
The system SHALL add a `HasRelatedFilter`-based "in use" filter to `DisciplineAdmin`, `TechniqueAdmin`, `ThemeAdmin`, `FormatAdmin`, `ScaleAdmin`, and `LocationAdmin`, filtering on whether the taxonomy is referenced by at least one artwork.

#### Scenario: Finding unused taxonomies
- **WHEN** an administrator opens a taxonomy changelist and selects the "sin obras" (without) lookup
- **THEN** only taxonomies not referenced by any artwork SHALL be shown.

#### Scenario: Finding used taxonomies
- **WHEN** an administrator opens a taxonomy changelist and selects the "con obras" (with) lookup
- **THEN** only taxonomies referenced by at least one artwork SHALL be shown.
