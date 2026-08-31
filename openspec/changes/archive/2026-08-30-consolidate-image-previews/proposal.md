# Consolidate Image Previews

## Why

The admin edit (change) form currently shows **two** image previews for the same image: the native Unfold file-input widget already renders a preview for any `ImageField`, and the project additionally renders custom readonly preview fields (`display_banner_preview` on `PostAdmin`, `display_preview_large` on `BlogImageAdmin`) immediately below it. This duplication is confusing and splits styling between Unfold's built-in widget and custom `.img-preview--banner` / `.img-preview--form` CSS classes.

## What Changes

- Remove the custom readonly form-field previews so the change form relies on **Unfold's native widget preview** as the single preview:
  - `PostAdmin.display_banner_preview` method, its entry in `readonly_fields`, and its entry in the `PostAdmin` fieldset.
  - `BlogImageAdmin.display_preview_large` method, its entry in `readonly_fields`, and its entry in the `BlogImageAdmin` fieldset.
  - `ArtworkImageInline.display_preview` method, its entry in `fields`, and its entry in `readonly_fields`.
- Remove the now-orphaned CSS classes `.img-preview--banner` and `.img-preview--form` from `static/css/style.css`. Keep `.img-preview`, `.img-preview--sm`, and `.img-preview--lg` (list-view thumbnails still use them).
- **Keep** list-view previews unchanged (`PostAdmin.display_banner`, `BlogImageAdmin.display_preview`, `ArtworkAdmin.display_image`) — they are not duplicated.
- Remove the obsolete unit tests for the deleted methods (`test_post_admin_display_banner_preview`, `test_blog_image_admin_display_preview_large`, `test_artwork_display_preview_class_and_no_inline_style`, `test_artwork_display_preview_fallback_empty`) and add regression tests asserting the change forms render exactly one preview source (Unfold's widget) and no `img-preview--banner` / `img-preview--form` / inline `display_preview` markup.
- Update the docs (`docs/django-unfold-admin.md`) and the affected OpenSpec specs to reflect the removal.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `admin-image-preview`: Remove the `--banner` and `--form` size-variant requirements; the shared class now covers only the thumbnail variants. Form-field previews (including inline form previews) are delegated to Unfold's native widget.
- `artwork-admin`: Remove the requirement that `ArtworkImageInline` renders a custom `display_preview` column; inline rows rely on Unfold's native widget preview.
- `blog-admin`: Remove the requirements that `PostAdmin` provides `display_banner_preview` and `BlogImageAdmin` provides `display_preview_large`; the change form preview requirement is satisfied by Unfold's native widget.

## Impact

- `blog/admin.py`: `PostAdmin` and `BlogImageAdmin` — remove readonly preview methods and fieldset references.
- `artworks/admin.py`: `ArtworkImageInline` — remove the `display_preview` readonly method and its field references.
- `static/css/style.css`: remove `.img-preview--banner` and `.img-preview--form`.
- `blog/tests.py`: remove 2 obsolete tests, add a change-form regression test.
- `artworks/tests.py`: remove 2 obsolete inline-preview tests.
- `docs/django-unfold-admin.md`: update the `.img-preview` section and usage guidance.
- `openspec/specs/admin-image-preview/spec.md`, `openspec/specs/artwork-admin/spec.md`, and `openspec/specs/blog-admin/spec.md`: requirement deltas.
- No model, migration, API, or template changes.