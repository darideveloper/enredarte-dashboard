# Artwork Admin Delta

## ADDED Requirements

### Requirement: Artwork list filters for artist, gallery, and year
The system SHALL add `artist`, `gallery` (via the `ArtworkGallery` through relation), and year (decade) filters to the `ArtworkAdmin` changelist.

#### Scenario: Filtering artworks by artist
- **WHEN** an administrator opens the Artwork changelist and selects an artist in the "Artista" filter
- **THEN** only artworks by that artist SHALL be shown.

#### Scenario: Artist filter shows only in-use artists
- **WHEN** an administrator opens the Artwork changelist and expands the "Artista" filter
- **THEN** only artists referenced by at least one artwork SHALL be listed.

#### Scenario: Filtering artworks by gallery
- **WHEN** an administrator opens the Artwork changelist and selects a gallery in the "Galería" filter
- **THEN** only artworks exhibited in that gallery SHALL be shown.

#### Scenario: Filtering artworks by decade
- **WHEN** an administrator opens the Artwork changelist and selects a decade in the "Año" filter
- **THEN** only artworks whose `year` falls within that decade SHALL be shown.

### Requirement: Artwork created_at date filter
The system SHALL add `created_at` to the `ArtworkAdmin` list filters so an administrator can filter artworks by creation date range.

#### Scenario: Filtering recently added artworks
- **WHEN** an administrator opens the Artwork changelist and applies a `created_at` date range
- **THEN** only artworks created within that range SHALL be shown.

## MODIFIED Requirements

### Requirement: List view display formatting
The system SHALL display the primary image thumbnail, localized title, artist, a taxonomy summary, formatted prices, and status in the Artwork changelist table, and filter by the taxonomy axes plus artist, gallery, year/decade, creation date, and discovery flags. The five taxonomy filters (`disciplines`, `techniques`, `themes`, `formats`, `scales`) SHALL use `RelatedOnlyFieldListFilter` so only taxonomies referenced by at least one artwork appear. The changelist SHALL paginate at 25 rows per page.

#### Scenario: Viewing the artwork catalog
- **WHEN** an administrator opens the Artwork list view
- **THEN** the table SHALL display an image preview thumbnail, translated title, artist name, the artwork's disciplines/temas summary, the formatted prices in MXN/USD, and the current status.

#### Scenario: Filtering the catalog
- **WHEN** an administrator uses the changelist filters
- **THEN** filtering by status, `is_active`, artist, gallery, year/decade, creation date, `is_highlighted`, disciplines, techniques, themes, formats, and scales is available (Surface is no longer a filter).

#### Scenario: Taxonomy filter shows only in-use values
- **WHEN** an administrator opens a taxonomy filter dropdown in the Artwork changelist
- **THEN** only taxonomies referenced by at least one artwork SHALL be listed.

#### Scenario: Artwork changelist pagination
- **WHEN** an administrator opens the Artwork changelist
- **THEN** at most 25 artworks SHALL be rendered per page.
