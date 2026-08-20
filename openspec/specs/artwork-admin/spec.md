# Artwork Admin Specification

## Purpose
To define the requirements for the Django Admin interface for managing Artwork entities, including translatable titles and descriptions, drag-and-drop sortable image galleries, gallery linkage, and commercial metadata.

## Requirements

### Requirement: Artwork model admin registration
The system SHALL register the `Artwork` model in `artworks/admin.py` using `ModelAdminUnfoldBase`.

#### Scenario: Viewing the admin sidebar
- **WHEN** an administrator opens the Django Admin panel
- **THEN** the sidebar SHALL list Artworks under the artworks application.

### Requirement: Bilingual translation inline
The system SHALL display `ArtworkTranslation` as a `StackedInline` inside the Artwork edit form, pre-populating Spanish (`es`) and English (`en`) forms during creation.

#### Scenario: Translating artwork details
- **WHEN** an administrator creates or edits an Artwork
- **THEN** they SHALL be able to edit Spanish and English titles and descriptions in the inline translation formset.

### Requirement: Drag-and-drop sortable images inline
The system SHALL display `ArtworkImage` as a `TabularInline` inside the Artwork edit form with drag-and-drop reordering via `sort_order`. Each row SHALL show an image preview rendered with the shared `.img-preview` class using no inline styles.

#### Scenario: Managing artwork images
- **WHEN** an administrator attaches images to an Artwork
- **THEN** they SHALL be able to upload images, set `alt_es` / `alt_en`, designate `is_primary`, and drag-and-drop to reorder images.

#### Scenario: Inline preview renders with shared class
- **WHEN** the `ArtworkImageInline` renders a row with an uploaded image
- **THEN** the preview `<img>` uses `class="img-preview"` and contains no inline `style=` attribute.

### Requirement: Form fieldsets and foreign key selection
The system SHALL group Artwork form fields into clean fieldsets and allow selecting `artist` plus the five taxonomy axes as ManyToMany: `disciplines`, `techniques`, `themes`, `formats`, and `scales`, rendered with `filter_horizontal`.

#### Scenario: Filling out artwork main data
- **WHEN** an administrator creates an Artwork
- **THEN** they SHALL be able to select the artist and one or more values for each axis — disciplines, techniques, themes, formats, and scales — and specify the year, dimensions, status, and prices in MXN and USD; no surface selector is shown.

#### Scenario: Multi-select taxonomy widgets
- **WHEN** an administrator opens the Artwork edit form
- **THEN** the five taxonomy fields render as `filter_horizontal` widgets and allow selecting several items per axis.

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

### Requirement: Discovery fields in the artwork form
The system SHALL add `is_highlighted` and `views_count` to the `ArtworkAdmin` edit form so an administrator can toggle featured status and set the views counter manually.

#### Scenario: Editing discovery fields
- **WHEN** an administrator opens an Artwork edit form
- **THEN** they can check `is_highlighted` and enter a `views_count` value.

### Requirement: Discovery fields in the artwork changelist and filters
The system SHALL display `is_highlighted` and `views_count` as columns in the `ArtworkAdmin` changelist and SHALL add `is_highlighted` as a list filter.

#### Scenario: Viewing and filtering discovery fields
- **WHEN** an administrator opens the Artwork changelist
- **THEN** they see highlighted state and views count per row and can filter by `is_highlighted`.

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
