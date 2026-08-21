## Context

With `Post`, `PostTranslation`, and `BlogImage` models established, the Django Admin must provide an intuitive, responsive interface built on Django Unfold. Editors must be able to write Spanish and English content together in one changeform, preview media, copy image links with a single click, auto-generate URL slugs from Spanish titles in real time, have publication dates pre-filled to current time in the UI, and benefit from pagination limits and query prefetching.

## Goals / Non-Goals

**Goals:**
- Implement `PostTranslationInline` (inheriting `StackedInline`) with `min_num=2`, `max_num=2`, `can_delete=False` using `TranslationInlineFormSet` to auto-initialize Spanish and English forms.
- Implement live client-side slug auto-population from Spanish title in `static/js/blog_slug_autofill.js` registered via `PostAdmin.Media`.
- Pre-fill `published_at = timezone.now()` and auto-increment `sort_order = max + 1` in `PostAdmin.get_changeform_initial_data()`.
- Add visual thumbnail previews (`display_banner` in list view, `display_banner_preview` in form view).
- Implement `BlogImageAdmin` with `sidebar_icon = "image"`, `list_per_page = 25`, image thumbnail preview (`display_preview`), and a one-click `copy_link` action with `copy_clipboard.js`.
- Add `date_hierarchy` to both admins (`published_at` for posts, `created_at` for images).
- Optimize changelist query performance with `prefetch_related("translations")`.

**Non-Goals:**
- Database migrations or model alterations (published_at pre-fill is handled cleanly at the UI/initial data layer).
- REST API serializers and endpoints (deferred to `blog-apis` proposal).
- Fixtures and testing (deferred to `blog-fixtures-tests` proposal).

## Decisions

### 1. Real-Time Client-Side Slug Generation
- **Decision**: Provide `static/js/blog_slug_autofill.js` that listens to `input` on `#id_translations-0-title` and normalizes the text into `#id_slug`.
- **Rationale**: Gives editors immediate visual confirmation of the slug as they type the Spanish title, while respecting manual overrides if `#id_slug` is edited directly. Backend `SlugBackfillMixin` serves as the fallback guarantee.

### 2. Publication Date UI Pre-Fill
- **Decision**: Pre-fill `published_at` with `timezone.now()` inside `PostAdmin.get_changeform_initial_data()`.
- **Rationale**: Achieves the desired default value for newly created posts in the admin form without modifying the model or generating a database migration.

### 3. Translation Inline Configuration
- **Decision**: Use `StackedInline` with `TranslationInlineFormSet` for `PostTranslationInline`.
- **Rationale**: Reuses the tested pattern from `artworks/admin.py` to ensure both language forms are pre-rendered and validated without manual language selection.

### 4. Clipboard Link Copying
- **Decision**: Implement `@action(description="Copiar enlace")` on `BlogImageAdmin` utilizing `get_media_url` and the `copy_to_clipboard` cookie pattern backed by `static/js/copy_clipboard.js`.
- **Rationale**: Reuses the documented pattern in `docs/django-image-copy-link.md` for seamless server-to-client clipboard copy.

### 5. Pagination Limits & Date Hierarchy
- **Decision**: Set `list_per_page = 25` and `date_hierarchy` on both `PostAdmin` and `BlogImageAdmin`.
- **Rationale**: Keeps database query execution and image rendering fast, aligning with `ArtworkAdmin`.

## Risks / Trade-offs

- **[Risk] N+1 Query in ChangeList**: Displaying translated titles in `PostAdmin` could cause separate queries per row.
  - **Mitigation**: Override `get_queryset()` to add `.prefetch_related("translations")` and resolve the Spanish title in Python.
