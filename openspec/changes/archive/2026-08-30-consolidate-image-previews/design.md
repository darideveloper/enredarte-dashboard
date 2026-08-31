# Design: Consolidate Image Previews

## Context

The Django admin uses Unfold. Unfold's native file-input widget (`clearable_file_input.html`) already renders an image preview for any `ImageField` that has an initial value. Independently, the project added custom readonly preview fields:

- `PostAdmin.display_banner_preview` (`img-preview--banner`, max-height 180px) — renders below the `banner_image` widget in the Post change form.
- `BlogImageAdmin.display_preview_large` (`img-preview--form`, max-height 240px) — renders below the `image` widget in the BlogImage change form.

Both cases show two previews of the same image, with styling split between Unfold's widget and custom CSS. `ArtworkImageInline.display_preview` likewise renders a preview column inside tabular inline rows alongside the `image` field's widget preview.

The list-view thumbnails (`PostAdmin.display_banner`, `BlogImageAdmin.display_preview`, `ArtworkAdmin.display_image`) are **not** duplicated and must remain.

## Goals / Non-Goals

**Goals:**
- Exactly one image preview per image, provided by Unfold's native widget (including inline rows).
- Preserve list-view thumbnails unchanged.
- Remove dead CSS classes and obsolete tests.
- Keep docs and OpenSpec specs coherent.

**Non-Goals:**
- Restyling Unfold's widget preview to the old `--banner` / `--form` sizes (Unfold's default is accepted).
- Touching models, migrations, APIs, or templates.
- Removing the `.img-preview--lg` class (kept as a reusable variant per decision).

## Decisions

### D1: Rely on Unfold's native widget for change-form previews
Remove the custom readonly preview fields and their fieldset entries. Unfold's `clearable_file_input.html` renders the preview whenever `accept="image/*"` (set by `ImageField`) and the field has an initial file.

- **Alternative considered**: Suppress Unfold's widget preview and keep custom fields (Option B) — rejected: requires template overrides, is more fragile across Unfold upgrades.
- **Alternative considered**: Keep both but hide one via CSS — rejected: fragile, and CSS-hiding a widget's preview is a hack.

### D2: Remove `ArtworkImageInline.display_preview`
Tabular inline rows show the `image` field's Unfold widget preview directly in the cell, so the additional `display_preview` column was redundant. Remove the method and its `fields` / `readonly_fields` entries so inline rows also have exactly one preview.

### D3: Remove orphaned CSS classes
Delete `.img-preview--banner` and `.img-preview--form` from `static/css/style.css`. Keep `.img-preview`, `.img-preview--sm`, `.img-preview--lg`. Update the `docs/django-unfold-admin.md` `.img-preview` section and usage paragraph accordingly.

### D4: Test strategy
Remove the obsolete unit tests (`test_post_admin_display_banner_preview`, `test_blog_image_admin_display_preview_large`, `test_artwork_display_preview_class_and_no_inline_style`, `test_artwork_display_preview_fallback_empty`). Add a regression test that renders the Post and BlogImage change forms and asserts they contain no `img-preview--banner` / `img-preview--form` markup (single preview source).

## Risks / Trade-offs

- [Change form preview is smaller than before] → Unfold's default sizing is accepted by decision; the preview is still functional and consistent with the rest of the admin.
- [Unfold widget rendering changes across versions] → No custom code depends on Unfold's widget internals, so upgrades are low-risk.
- [Regression test relies on Unfold's change-form markup] → The assertion is on *absence* of custom classes (our own markup), not on Unfold internals, so it stays robust.

## Migration Plan

No data migration. Deployment is a single code change; rollback is reverting the commit. The specs (`admin-image-preview`, `blog-admin`) receive deltas at archive time via the normal OpenSpec workflow.

## Open Questions

None.