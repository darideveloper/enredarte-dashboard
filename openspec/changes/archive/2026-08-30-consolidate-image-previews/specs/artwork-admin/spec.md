# artwork-admin Spec Deltas

## MODIFIED Requirements

### Requirement: Drag-and-drop sortable images inline
The system SHALL display `ArtworkImage` as a `TabularInline` inside the Artwork edit form with drag-and-drop reordering via `sort_order`. Each row's image preview SHALL be provided by Unfold's native file-input widget; no custom `display_preview` readonly column is rendered.

#### Scenario: Managing artwork images
- **WHEN** an administrator attaches images to an Artwork
- **THEN** they SHALL be able to upload images, set `alt_es` / `alt_en`, designate `is_primary`, and drag-and-drop to reorder images.

#### Scenario: Inline image preview comes from Unfold's widget
- **WHEN** the `ArtworkImageInline` renders a row with an uploaded image
- **THEN** the preview is rendered by Unfold's native file-input widget and SHALL NOT include a custom `display_preview` column or `class="img-preview"` markup emitted by the inline.