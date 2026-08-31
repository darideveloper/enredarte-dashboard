# admin-image-preview Spec Deltas

## MODIFIED Requirements

### Requirement: Size variants for thumbnails
The system SHALL provide `.img-preview--sm` (small) and `.img-preview--lg` (large) modifiers in addition to the regular `.img-preview` class so distinct list-view and inline thumbnails can use different sizes while reusing the base class. Form-field previews SHALL NOT use custom size variants: the change form relies on Unfold's native file-input widget preview.

#### Scenario: Small thumbnail variant
- **WHEN** an element uses `class="img-preview img-preview--sm"`
- **THEN** it renders as a small square thumbnail (40px, object-fit cover) while sharing the base `.img-preview` shape

#### Scenario: Large thumbnail variant
- **WHEN** an element uses `class="img-preview img-preview--lg"`
- **THEN** it renders as a large square thumbnail (64px, object-fit cover) while sharing the base `.img-preview` shape

#### Scenario: Regular thumbnail default
- **WHEN** an element uses `class="img-preview"` with no size variant
- **THEN** it renders at the regular size (50px, object-fit cover)

#### Scenario: Form-field preview uses Unfold's native widget
- **WHEN** the admin change form renders an `ImageField`
- **THEN** the preview is rendered by Unfold's native file-input widget and SHALL NOT use the `img-preview--banner` or `img-preview--form` classes

### Requirement: Preview renderers emit class only
Every admin image-preview renderer across all applications SHALL emit an `<img>` with the `img-preview` class (and a size variant when a non-default size is needed), with no inline style attributes.

#### Scenario: No inline styles in renderers
- **WHEN** any preview renderer in `artworks/admin.py` or `blog/admin.py` returns the image preview markup
- **THEN** the returned markup contains `class="img-preview"` (or an appropriate modifier variant) and no `style=` attribute

#### Scenario: Changelist previews emit img-preview class only
- **WHEN** `PostAdmin.display_banner`, `BlogImageAdmin.display_preview`, or `ArtworkAdmin.display_image` returns the preview markup
- **THEN** the returned markup contains `class="img-preview"` (with the appropriate `--sm` variant where applicable) and no `style=` attribute