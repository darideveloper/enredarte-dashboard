## MODIFIED Requirements

### Requirement: List view display formatting
The system SHALL display the primary image thumbnail, localized title, status, active state, artist, a truncated taxonomy summary (at most ~60 characters with ellipsis in the list; full text on the change form), formatted prices, and highlighted state in the Artwork changelist table, in that column order, and filter by the taxonomy axes plus artist, gallery, year/decade, creation date, and discovery flags. The five taxonomy filters (`disciplines`, `techniques`, `themes`, `formats`, `scales`) SHALL use `RelatedOnlyFieldListFilter` so only taxonomies referenced by at least one artwork appear. The changelist SHALL paginate at 25 rows per page. The image preview thumbnail SHALL render with the shared `.img-preview img-preview--sm` classes using no inline styles.

#### Scenario: Viewing the artwork catalog
- **WHEN** an administrator opens the Artwork list view
- **THEN** the table SHALL display, in order, an image preview thumbnail rendered with the `.img-preview img-preview--sm` classes (no inline styles), translated title, current status, active state, artist name, the truncated disciplines/temas summary, the formatted prices in MXN/USD, and the highlighted state.

#### Scenario: Filtering the catalog
- **WHEN** an administrator uses the changelist filters
- **THEN** filtering by status, `is_active`, artist, gallery, year/decade, creation date, `is_highlighted`, disciplines, techniques, themes, formats, and scales is available (Surface is no longer a filter).

#### Scenario: Taxonomy filter shows only in-use values
- **WHEN** an administrator opens a taxonomy filter dropdown in the Artwork changelist
- **THEN** only taxonomies referenced by at least one artwork SHALL be listed.

#### Scenario: Artwork changelist pagination
- **WHEN** an administrator opens the Artwork changelist
- **THEN** at most 25 artworks SHALL be rendered per page.

### Requirement: Discovery fields in the artwork changelist and filters
The system SHALL display `is_highlighted` as a column in the `ArtworkAdmin` changelist and SHALL expose `is_highlighted` as a list filter. `views_count` SHALL remain editable on the change form and SHALL NOT appear as a changelist column.

#### Scenario: Viewing and filtering discovery fields
- **WHEN** an administrator opens the Artwork changelist
- **THEN** they see highlighted state per row and can filter by `is_highlighted`; views count is visible on the change form, not in the list.
