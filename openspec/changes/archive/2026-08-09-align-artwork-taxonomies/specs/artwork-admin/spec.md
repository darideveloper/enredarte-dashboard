## MODIFIED Requirements

### Requirement: Form fieldsets and foreign key selection

The system SHALL group Artwork form fields into clean fieldsets and allow selecting `artist` plus the five taxonomy axes as ManyToMany: `disciplines`, `techniques`, `themes`, `formats`, and `scales`, rendered with `filter_horizontal`.

#### Scenario: Filling out artwork main data

- **WHEN** an administrator creates an Artwork
- **THEN** they SHALL be able to select the artist and one or more values for each axis — disciplines, techniques, themes, formats, and scales — and specify the year, dimensions, status, and prices in MXN and USD; no surface selector is shown.

#### Scenario: Multi-select taxonomy widgets

- **WHEN** an administrator opens the Artwork edit form
- **THEN** the five taxonomy fields render as `filter_horizontal` widgets and allow selecting several items per axis.

### Requirement: List view display formatting

The system SHALL display the primary image thumbnail, localized title, artist, a taxonomy summary, formatted prices, and status in the Artwork changelist table, and filter by the new taxonomy axes.

#### Scenario: Viewing the artwork catalog

- **WHEN** an administrator opens the Artwork list view
- **THEN** the table SHALL display an image preview thumbnail, translated title, artist name, the artwork's disciplines/temas summary, the formatted prices in MXN/USD, and the current status.

#### Scenario: Filtering the catalog

- **WHEN** an administrator uses the changelist filters
- **THEN** filtering by status, `is_active`, disciplines, techniques, themes, formats, and scales is available (Surface is no longer a filter).