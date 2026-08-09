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
The system SHALL display `ArtworkImage` as a `TabularInline` inside the Artwork edit form with drag-and-drop reordering via `sort_order`.

#### Scenario: Managing artwork images
- **WHEN** an administrator attaches images to an Artwork
- **THEN** they SHALL be able to upload images, set `alt_es` / `alt_en`, designate `is_primary`, and drag-and-drop to reorder images.

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
