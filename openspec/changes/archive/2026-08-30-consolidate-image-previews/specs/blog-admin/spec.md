# blog-admin Spec Deltas

## MODIFIED Requirements

### Requirement: Post Admin Interface with Translation Inlines and Live Slug Auto-fill
The system SHALL register `Post` in Django Admin using Unfold with single-screen multilingual editing, live slug generation from Spanish title, and pre-filled publication date. The interface SHALL NOT display or manage a `sort_order` field. The changelist image preview SHALL use the `.img-preview` class with no inline styles; the change form image preview SHALL be provided by Unfold's native file-input widget (no custom readonly preview field).

#### Scenario: PostAdmin configuration and inlines
- **WHEN** `PostAdmin` is registered in `blog/admin.py`
- **THEN** it inherits from `ModelAdminUnfoldBase` and defines `sidebar_icon = "article"`
- **AND** it includes `PostTranslationInline` inheriting `StackedInline` with `min_num = 2`, `max_num = 2`, and `can_delete = False`
- **AND** it sets `list_per_page = 25`, `date_hierarchy = "published_at"`, and prefetches `translations` in `get_queryset()`
- **AND** it provides `display_banner` emitting `class="img-preview img-preview--sm"` with no inline `style=` attributes
- **AND** it SHALL NOT provide a `display_banner_preview` readonly field in the change form
- **AND** it SHALL NOT include `sort_order` in `fieldsets` or `list_display`

#### Scenario: Changeform initial data and live slug script
- **WHEN** the `PostAdmin` add form is loaded
- **THEN** `get_changeform_initial_data()` SHALL pre-fill `published_at` with the current time
- **AND** it SHALL NOT calculate or pre-fill `sort_order`
- **AND** `static/js/blog_slug_autofill.js` SHALL be loaded to auto-populate the slug field from the Spanish title in real time

### Requirement: BlogImage Admin Interface with Preview and Copy Action
The system SHALL register `BlogImage` in Django Admin with date hierarchy and a client-side clipboard copy button. The changelist image preview SHALL use the `.img-preview` class with no inline styles; the change form image preview SHALL be provided by Unfold's native file-input widget (no custom readonly preview field). The copy button SHALL be a custom-injected `<button>` in the change form header (rendered through Unfold's button component) that copies the absolute image URL on click, without any server round-trip or cookie.

#### Scenario: BlogImageAdmin configuration and copy link action
- **WHEN** `BlogImageAdmin` is registered in `blog/admin.py`
- **THEN** it inherits from `ModelAdminUnfoldBase` and defines `sidebar_icon = "image"`
- **AND** it sets `list_per_page = 25` and `date_hierarchy = "created_at"`
- **AND** it provides a `display_preview` method emitting `class="img-preview img-preview--sm"` with no inline `style=` attributes
- **AND** it SHALL NOT provide a `display_preview_large` readonly field in the change form
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