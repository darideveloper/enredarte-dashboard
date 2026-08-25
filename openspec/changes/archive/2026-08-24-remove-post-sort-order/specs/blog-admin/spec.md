## MODIFIED Requirements

### Requirement: Post Admin Interface with Translation Inlines and Live Slug Auto-fill
The system SHALL register `Post` in Django Admin using Unfold with single-screen multilingual editing, live slug generation from Spanish title, and pre-filled publication date. The interface SHALL NOT display or manage a `sort_order` field.

#### Scenario: PostAdmin configuration and inlines
- **WHEN** `PostAdmin` is registered in `blog/admin.py`
- **THEN** it inherits from `ModelAdminUnfoldBase` and defines `sidebar_icon = "article"`
- **AND** it includes `PostTranslationInline` inheriting `StackedInline` with `min_num = 2`, `max_num = 2`, and `can_delete = False`
- **AND** it sets `list_per_page = 25`, `date_hierarchy = "published_at"`, and prefetches `translations` in `get_queryset()`
- **AND** it provides `display_banner` in list view and `display_banner_preview` in change form
- **AND** it SHALL NOT include `sort_order` in `fieldsets` or `list_display`

#### Scenario: Changeform initial data and live slug script
- **WHEN** the `PostAdmin` add form is loaded
- **THEN** `get_changeform_initial_data()` SHALL pre-fill `published_at` with the current time
- **AND** it SHALL NOT calculate or pre-fill `sort_order`
- **AND** `static/js/blog_slug_autofill.js` SHALL be loaded to auto-populate the slug field from the Spanish title in real time
