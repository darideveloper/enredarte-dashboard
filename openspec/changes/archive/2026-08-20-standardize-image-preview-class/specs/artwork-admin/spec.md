## MODIFIED Requirements

### Requirement: List view display formatting
The system SHALL display the primary image thumbnail, localized title, artist, a taxonomy summary, formatted prices, and status in the Artwork changelist table, and filter by the taxonomy axes plus artist, gallery, year/decade, creation date, and discovery flags. The five taxonomy filters (`disciplines`, `techniques`, `themes`, `formats`, `scales`) SHALL use `RelatedOnlyFieldListFilter` so only taxonomies referenced by at least one artwork appear. The changelist SHALL paginate at 25 rows per page. The image preview thumbnail SHALL render with the shared `.img-preview img-preview--sm` classes using no inline styles.

#### Scenario: Viewing the artwork catalog
- **WHEN** an administrator opens the Artwork list view
- **THEN** the table SHALL display an image preview thumbnail rendered with the `.img-preview img-preview--sm` classes (no inline styles), translated title, artist name, the artwork's disciplines/temas summary, the formatted prices in MXN/USD, and the current status.

#### Scenario: Filtering the catalog
- **WHEN** an administrator uses the changelist filters
- **THEN** filtering by status, `is_active`, artist, gallery, year/decade, creation date, `is_highlighted`, disciplines, techniques, themes, formats, and scales is available (Surface is no longer a filter).

#### Scenario: Taxonomy filter shows only in-use values
- **WHEN** an administrator opens a taxonomy filter dropdown in the Artwork changelist
- **THEN** only taxonomies referenced by at least one artwork SHALL be listed.

#### Scenario: Artwork changelist pagination
- **WHEN** an administrator opens the Artwork changelist
- **THEN** at most 25 artworks SHALL be rendered per page.

### Requirement: Drag-and-drop sortable images inline
The system SHALL display `ArtworkImage` as a `TabularInline` inside the Artwork edit form with drag-and-drop reordering via `sort_order`. Each row SHALL show an image preview rendered with the shared `.img-preview` class using no inline styles.

#### Scenario: Managing artwork images
- **WHEN** an administrator attaches images to an Artwork
- **THEN** they SHALL be able to upload images, set `alt_es` / `alt_en`, designate `is_primary`, and drag-and-drop to reorder images.

#### Scenario: Inline preview renders with shared class
- **WHEN** the `ArtworkImageInline` renders a row with an uploaded image
- **THEN** the preview `<img>` uses `class="img-preview"` and contains no inline `style=` attribute.
