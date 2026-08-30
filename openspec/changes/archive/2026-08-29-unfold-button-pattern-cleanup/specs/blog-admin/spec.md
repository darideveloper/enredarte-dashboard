## MODIFIED Requirements

### Requirement: BlogImage Admin Interface with Preview and Copy Action
The system SHALL register `BlogImage` in Django Admin with image preview, date hierarchy, and a client-side clipboard copy button, with all image previews styled via `.img-preview` CSS classes without inline styles. The copy button SHALL be a custom-injected `<button>` in the change form header (rendered through Unfold's button component) that copies the absolute image URL on click, without any server round-trip or cookie.

#### Scenario: BlogImageAdmin configuration and copy link action
- **WHEN** `BlogImageAdmin` is registered in `blog/admin.py`
- **THEN** it inherits from `ModelAdminUnfoldBase` and defines `sidebar_icon = "image"`
- **AND** it sets `list_per_page = 25` and `date_hierarchy = "created_at"`
- **AND** it provides a `display_preview` method emitting `class="img-preview img-preview--sm"` and `display_preview_large` emitting `class="img-preview--form"`, both with no inline `style=` attributes
- **AND** it SHALL NOT register a `copy_link` row action that sets a cookie
- **AND** it includes `js/copy_clipboard.js` in `Media`

#### Scenario: Change form shows a copy button with the image URL preloaded
- **WHEN** an administrator opens a `BlogImage` change form for an image
- **THEN** a "Copiar enlace" button SHALL appear in the header, rendered with Unfold's button component, carrying the absolute image URL in its `data-copy-url` attribute

#### Scenario: Clicking copy writes to clipboard
- **WHEN** an administrator clicks the "Copiar enlace" button
- **THEN** the `data-copy-url` value SHALL be written to the clipboard and the button label SHALL briefly display "¡Copiado!" without removing the button icon

#### Scenario: Change form without an image shows no copy button
- **WHEN** an administrator opens a `BlogImage` change form and the image has no file
- **THEN** no copy button SHALL be rendered