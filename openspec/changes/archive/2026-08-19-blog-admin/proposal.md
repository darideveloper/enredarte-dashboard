## Why

Following the creation of the blog models, administrators need an ergonomic, responsive Django Admin interface to manage blog posts and media assets. The admin must allow editing Spanish and English translations on a single screen without manual language selection, auto-populate the slug from the Spanish title in real time as the user types, pre-fill the publication date to now in the UI while keeping it editable, provide live image previews and one-click URL copying for uploaded assets, and enforce pagination limits (`list_per_page = 25`) to ensure high performance.

## What Changes

- Create `static/js/blog_slug_autofill.js` for real-time client-side slug generation from the Spanish title input into the parent slug field.
- Implement `PostAdmin` in `blog/admin.py`:
  - Register `PostTranslationInline` (inheriting `StackedInline`) with automatic language formset (`es` and `en`) and validation.
  - Pre-fill `published_at = timezone.now()` and auto-increment `sort_order = max_order + 1` via `get_changeform_initial_data()`.
  - Include `js/blog_slug_autofill.js` in `PostAdmin.Media` for live typing slug auto-population.
  - Add `display_banner` (40x40 thumbnail) to `list_display` and `display_banner_preview` to `readonly_fields` in the change form.
  - Divide fields into structured full-width fieldsets: general metadata (`"author"`, `"published_at"`, `"banner_image"`, `"display_banner_preview"`) and system attributes (`"slug"`, `("is_active", "sort_order")`).
  - Add search fields (`slug`, `translations__title`, `translations__description`, `translations__keywords`, `author`), filters (`is_active`, `created_at`, `published_at`, `author`), and date hierarchy (`date_hierarchy = "published_at"`).
  - Set `list_per_page = 25` and optimize changelist query performance via `.prefetch_related("translations")`.
  - Configure sidebar icon `sidebar_icon = "article"`.
- Implement `BlogImageAdmin` in `blog/admin.py`:
  - Display image thumbnail previews (`display_preview` 48x48 in list, `display_preview_large` in form).
  - Implement a `copy_link` row action utilizing `get_media_url` and `copy_clipboard.js` to copy the image URL directly to the clipboard with one click.
  - Add `date_hierarchy = "created_at"` and set `list_per_page = 25`.
  - Configure sidebar icon `sidebar_icon = "image"`.

## Capabilities

### New Capabilities
- `blog-admin`: Django Unfold Admin customization and management views for blog posts, live slug generation, translations, and media images.

### Modified Capabilities
<!-- None -->

## Impact

- `static/js/blog_slug_autofill.js`: New client-side live slug sync script.
- `blog/admin.py`: Defines `PostAdmin`, `PostTranslationInline`, and `BlogImageAdmin`.
- Integrates seamlessly with Unfold theme, auto sidebar navigation, and `copy_clipboard.js`.
