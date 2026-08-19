# Gallery Admin Specification

## Purpose
To define the requirements for the Django Admin interface for managing Gallery entities, including translation support and drag-and-drop artwork curation.

## Requirements

### Requirement: Gallery model admin registration
The system SHALL register the `Gallery` model in `artworks/admin.py` using `ModelAdminUnfoldBase`.

#### Scenario: Viewing the admin sidebar
- **WHEN** an administrator opens the Django Admin panel
- **THEN** the sidebar SHALL list Galleries under the artworks application.

### Requirement: Bilingual translation inline
The system SHALL display `GalleryTranslation` as a `StackedInline` inside the Gallery edit form, pre-populating Spanish (`es`) and English (`en`) forms during creation and suppressing extras when translations exist.

#### Scenario: Creating a new gallery
- **WHEN** an administrator creates a new Gallery
- **THEN** the translation inline forms SHALL render with default language selections set to Spanish and English.

### Requirement: Gallery list view display name
The system SHALL display the localized name (preferring Spanish, then falling back to the first available translation) in the changelist view for Galleries.

#### Scenario: Viewing the list of Galleries
- **WHEN** an administrator views the Gallery changelist
- **THEN** the table SHALL display the gallery's translated name in the "Nombre" column.

### Requirement: Drag-and-drop sortable artworks inline
The system SHALL display `ArtworkGallery` as a `TabularInline` inside the Gallery edit form. This inline MUST support drag-and-drop sorting via the `sort_order` field.

#### Scenario: Curating a gallery's artworks
- **GIVEN** a Gallery exists with multiple Artworks
- **WHEN** an administrator edits the Gallery
- **THEN** they SHALL see a tabular list of associated artworks
- **AND** they SHALL be able to drag and drop rows to reorder them without manually typing integer values into the `sort_order` field.

### Requirement: Gallery curator filter
The system SHALL add a `curator` filter to the `GalleryAdmin` changelist so an administrator can browse galleries by their assigned `ArtCurator`.

#### Scenario: Filtering galleries by curator
- **WHEN** an administrator opens the Gallery changelist and selects a curator in the "Curador" filter
- **THEN** only galleries curated by that curator SHALL be shown.

#### Scenario: Curator filter shows only in-use curators
- **WHEN** an administrator opens the Gallery changelist and expands the "Curador" filter
- **THEN** only curators curating at least one gallery SHALL be listed.

### Requirement: Gallery has-artworks filter
The system SHALL add a "with/without artworks" filter to the `GalleryAdmin` changelist so an administrator can identify galleries that are empty (no exhibited artworks).

#### Scenario: Finding empty galleries
- **WHEN** an administrator opens the Gallery changelist and selects the "sin obras" lookup
- **THEN** only galleries with no `ArtworkGallery` links SHALL be shown.

#### Scenario: Finding galleries with artworks
- **WHEN** an administrator opens the Gallery changelist and selects the "con obras" lookup
- **THEN** only galleries with at least one exhibited artwork SHALL be shown.

### Requirement: Gallery admin exposes primary flag
The `GalleryAdmin` edit form SHALL include the `is_primary` boolean field so an administrator can mark a gallery as the main gallery of the collection.

#### Scenario: Editing a gallery shows the primary field
- **WHEN** an administrator edits a Gallery
- **THEN** the "Información básica" fieldset SHALL include the "Galería principal" checkbox.

### Requirement: Gallery changelist shows and filters by primary flag
The `GalleryAdmin` changelist SHALL display the `is_primary` flag as a column and provide a filter for it.

#### Scenario: Viewing the Gallery changelist
- **WHEN** an administrator views the Gallery changelist
- **THEN** the table SHALL show a column reflecting whether each gallery is primary.

#### Scenario: Filtering galleries by primary flag
- **WHEN** an administrator opens the Gallery changelist and selects the primary flag filter
- **THEN** the list SHALL be filtered to galleries with that `is_primary` value.
