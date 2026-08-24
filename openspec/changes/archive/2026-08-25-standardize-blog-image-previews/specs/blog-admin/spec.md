## MODIFIED Requirements

### Requirement: Post Admin Interface with Translation Inlines and Live Slug Auto-fill
The system SHALL register `Post` in Django Admin using Unfold with single-screen multilingual editing, live slug generation from Spanish title, and pre-filled publication date. The interface SHALL NOT display or manage a `sort_order` field, and all image previews SHALL use `.img-preview` classes with no inline styles.

#### Scenario: PostAdmin configuration and inlines
- **WHEN** `PostAdmin` is registered in `blog/admin.py`
- **THEN** it inherits from `ModelAdminUnfoldBase` and defines `sidebar_icon = "article"`
- **AND** it includes `PostTranslationInline` inheriting `StackedInline` with `min_num = 2`, `max_num = 2`, and `can_delete = False`
- **AND** it sets `list_per_page = 25`, `date_hierarchy = "published_at"`, and prefetches `translations` in `get_queryset()`
- **AND** it provides `display_banner` emitting `class="img-preview img-preview--sm"` and `display_banner_preview` emitting `class="img-preview--banner"`, both with no inline `style=` attributes
- **AND** it SHALL NOT include `sort_order` in `fieldsets` or `list_display`

#### Scenario: Changeform initial data and live slug script
- **WHEN** the `PostAdmin` add form is loaded
- **THEN** `get_changeform_initial_data()` SHALL pre-fill `published_at` with the current time
- **AND** it SHALL NOT calculate or pre-fill `sort_order`
- **AND** `static/js/blog_slug_autofill.js` SHALL be loaded to auto-populate the slug field from the Spanish title in real time

### Requirement: BlogImage Admin Interface with Preview and Copy Action
The system SHALL register `BlogImage` in Django Admin with image preview, date hierarchy, and clipboard copy action, with all image previews styled via `.img-preview` CSS classes without inline styles.

#### Scenario: BlogImageAdmin configuration and copy link action
- **WHEN** `BlogImageAdmin` is registered in `blog/admin.py`
- **THEN** it inherits from `ModelAdminUnfoldBase` and defines `sidebar_icon = "image"`
- **AND** it sets `list_per_page = 25` and `date_hierarchy = "created_at"`
- **AND** it provides a `display_preview` method emitting `class="img-preview img-preview--sm"` and `display_preview_large` emitting `class="img-preview--form"`, both with no inline `style=` attributes
- **AND** it provides a `copy_link` action setting the `copy_to_clipboard` cookie and including `js/copy_clipboard.js` in `Media`
