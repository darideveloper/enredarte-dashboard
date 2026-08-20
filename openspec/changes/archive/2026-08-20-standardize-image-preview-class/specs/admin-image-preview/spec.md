## ADDED Requirements

### Requirement: Shared image preview CSS class
The system SHALL provide a single `.img-preview` CSS class in `static/css/style.css` that defines the sizing and shape (height, width, border-radius, object-fit) of every admin image preview thumbnail.

#### Scenario: Preview styling comes from CSS only
- **WHEN** any admin page renders an element with `class="img-preview"`
- **THEN** its size and shape are fully defined by the `.img-preview` rule in `static/css/style.css` and no inline `style=` attribute is required

#### Scenario: Styling is not JS-injected
- **WHEN** the admin page loads and JavaScript executes
- **THEN** no JavaScript adds Tailwind utility classes to `.img-preview` elements for sizing or shape

### Requirement: Size variants for thumbnails
The system SHALL provide `.img-preview--sm` (small) and `.img-preview--lg` (large) modifiers in addition to the regular `.img-preview` class so distinct previews can use different sizes while reusing the base class.

#### Scenario: Small thumbnail variant
- **WHEN** an element uses `class="img-preview img-preview--sm"`
- **THEN** it renders as a small square thumbnail (40px, object-fit cover) while sharing the base `.img-preview` shape

#### Scenario: Large thumbnail variant
- **WHEN** an element uses `class="img-preview img-preview--lg"`
- **THEN** it renders as a large square thumbnail (64px, object-fit cover) while sharing the base `.img-preview` shape

#### Scenario: Regular thumbnail default
- **WHEN** an element uses `class="img-preview"` with no size variant
- **THEN** it renders at the regular size (50px, object-fit cover)

### Requirement: Preview renderers emit class only
Every admin image-preview renderer SHALL emit an `<img>` with the `img-preview` class (and a size variant when a non-default size is needed), with no inline style attributes.

#### Scenario: No inline styles in renderers
- **WHEN** a preview renderer in `artworks/admin.py` returns the thumbnail markup
- **THEN** the returned markup contains `class="img-preview"` (with a size variant when applicable) and no `style=` attribute
