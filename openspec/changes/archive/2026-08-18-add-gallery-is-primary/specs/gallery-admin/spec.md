## ADDED Requirements

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
