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
