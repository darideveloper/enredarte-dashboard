## MODIFIED Requirements

### Requirement: Size variants for thumbnails
The system SHALL provide `.img-preview--sm` (small), `.img-preview--lg` (large), `.img-preview--banner` (banner preview), and `.img-preview--form` (form preview) modifiers in addition to the regular `.img-preview` class so distinct previews can use different sizes while reusing the base class.

#### Scenario: Small thumbnail variant
- **WHEN** an element uses `class="img-preview img-preview--sm"`
- **THEN** it renders as a small square thumbnail (40px, object-fit cover) while sharing the base `.img-preview` shape

#### Scenario: Large thumbnail variant
- **WHEN** an element uses `class="img-preview img-preview--lg"`
- **THEN** it renders as a large square thumbnail (64px, object-fit cover) while sharing the base `.img-preview` shape

#### Scenario: Banner preview variant
- **WHEN** an element uses `class="img-preview--banner"`
- **THEN** it renders with max-height 180px, max-width 100%, border-radius 8px, and object-fit cover

#### Scenario: Form preview variant
- **WHEN** an element uses `class="img-preview--form"`
- **THEN** it renders with max-height 240px, max-width 100%, border-radius 8px, and object-fit cover

#### Scenario: Regular thumbnail default
- **WHEN** an element uses `class="img-preview"` with no size variant
- **THEN** it renders at the regular size (50px, object-fit cover)

### Requirement: Preview renderers emit class only
Every admin image-preview renderer across all applications SHALL emit an `<img>` with the `img-preview` class (and a size variant when a non-default size is needed), with no inline style attributes.

#### Scenario: No inline styles in renderers
- **WHEN** any preview renderer in `artworks/admin.py` or `blog/admin.py` returns the image preview markup
- **THEN** the returned markup contains `class="img-preview"` (or an appropriate modifier variant) and no `style=` attribute
