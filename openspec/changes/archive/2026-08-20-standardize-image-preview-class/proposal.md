## Why

Image preview thumbnails in the Django Admin (`artworks/admin.py`) duplicate sizing and shape rules between the `img-preview` CSS hook and inline `style=` attributes on each `<img>`. The two usages disagree (50px vs 40px), and the JS-injected Tailwind classes (`h-16 rounded-xl object-cover`) are dead where inline styles win, so styling is inconsistent, redundant, and unclear.

## What Changes

- Define `.img-preview` as real CSS in `static/css/style.css`, making it the single source of truth for thumbnail sizing and shape (no inline `style=` attributes).
- Provide three size variants as real CSS: base `.img-preview` (regular), `.img-preview--sm` (small, 40px square for the list thumbnail), and `.img-preview--lg` (large).
- Update the two renderers in `artworks/admin.py` to emit `class="img-preview"` plus a size variant when needed, with no inline styles.
- Remove the `.img-preview` entry from `static/js/add_tailwind_styles.js` since styling now lives in CSS.
- Update the docs (`docs/django-unfold-admin.md`) so the documented convention matches the implementation.

## Capabilities

### New Capabilities
- `admin-image-preview`: the single, reusable `.img-preview` CSS class with regular/small/large size variants, used by all admin image preview thumbnails, without inline styles or JS-injected classes.

### Modified Capabilities
- `artwork-admin`: the Artwork changelist image preview thumbnail and the `ArtworkImageInline` preview now render with the shared `.img-preview` class instead of per-tag inline styles.

## Impact

- `static/css/style.css` — add `.img-preview` (and `--sm`, `--lg` variant) rules.
- `static/js/add_tailwind_styles.js` — remove the `.img-preview` selector entry.
- `artworks/admin.py` — `display_image` (line ~646) and `ArtworkImageInline.display_preview` (line ~563) drop inline styles and use `class="img-preview"`.
- `docs/django-unfold-admin.md` — update the documented `.img-preview` convention.
- No model, migration, or template changes; no external dependencies.
