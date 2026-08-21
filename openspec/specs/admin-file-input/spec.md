## ADDED Requirements

### Requirement: File input label text is fully visible
The Django admin file/image upload widgets SHALL render the fake filename `<input type="text">` at the full width of the widget container so the placeholder text ("Seleccionar archivo para subir") is not truncated or clipped.

#### Scenario: Change form file field renders full-width
- **WHEN** an admin change form with a file/image field (an `ImageField` or a `FileField`, where present) loads
- **THEN** the disabled text input inside the file widget spans 100% of the widget width and the full label text is visible

#### Scenario: Inline form file field renders full-width
- **WHEN** an admin inline form with a file/image field (currently only `ArtworkImageInline` in this project) loads
- **THEN** the small file widget's disabled text input spans the widget width and the full label text is visible

### Requirement: Fix is applied to all file inputs in one place
The width fix SHALL be implemented once and apply to every file upload widget rendered by Unfold, without modifying Unfold templates or adding per-field code.

#### Scenario: Single shared stylesheet rule
- **WHEN** the admin loads any page that renders a file upload widget
- **THEN** the widget styling comes from the shared `static/css/style.css` and no file field requires individual CSS or template overrides

#### Scenario: Selector does not affect other inputs
- **WHEN** the shared stylesheet is applied to an admin page
- **THEN** text inputs outside the file upload widgets (regular text fields, readonly fields) keep their existing width behavior
