# blog-admin Specification

## Purpose
TBD - created by archiving change blog-admin. Update Purpose after archive.
## Requirements
### Requirement: Post Admin Interface with Translation Inlines and Live Slug Auto-fill
The system SHALL register `Post` in Django Admin using Unfold with single-screen multilingual editing, live slug generation from Spanish title, and pre-filled publication date.

#### Scenario: PostAdmin configuration and inlines
- **WHEN** `PostAdmin` is registered in `blog/admin.py`
- **THEN** it inherits from `ModelAdminUnfoldBase` and defines `sidebar_icon = "article"`
- **AND** it includes `PostTranslationInline` inheriting `StackedInline` with `min_num = 2`, `max_num = 2`, and `can_delete = False`
- **AND** it sets `list_per_page = 25`, `date_hierarchy = "published_at"`, and prefetches `translations` in `get_queryset()`
- **AND** it provides `display_banner` in list view and `display_banner_preview` in change form

#### Scenario: Changeform initial data and live slug script
- **WHEN** the `PostAdmin` add form is loaded
- **THEN** `get_changeform_initial_data()` SHALL pre-fill `published_at` with the current time and `sort_order` with `max_order + 1`
- **AND** `static/js/blog_slug_autofill.js` SHALL be loaded to auto-populate the slug field from the Spanish title in real time

### Requirement: BlogImage Admin Interface with Preview and Copy Action
The system SHALL register `BlogImage` in Django Admin with image preview, date hierarchy, and clipboard copy action.

#### Scenario: BlogImageAdmin configuration and copy link action
- **WHEN** `BlogImageAdmin` is registered in `blog/admin.py`
- **THEN** it inherits from `ModelAdminUnfoldBase` and defines `sidebar_icon = "image"`
- **AND** it sets `list_per_page = 25` and `date_hierarchy = "created_at"`
- **AND** it provides a `display_preview` method rendering an `<img>` tag thumbnail and `display_preview_large` in form view
- **AND** it provides a `copy_link` action setting the `copy_to_clipboard` cookie and including `js/copy_clipboard.js` in `Media`

