## 1. CSS: shared `.img-preview` class

- [x] 1.1 Add base `.img-preview` rule to `static/css/style.css` (height 50px, border-radius 6px, object-fit cover) as the single source of truth for preview shape/size.
- [x] 1.2 Add `.img-preview--sm` modifier (height 40px, width 40px, object-fit cover) for the small square list thumbnail.
- [x] 1.3 Add `.img-preview--lg` modifier (height 64px, width 64px, object-fit cover) for large square previews.

## 2. JS: remove injected preview styling

- [x] 2.1 Remove the `.img-preview` entry from the `classes` array in `static/js/add_tailwind_styles.js`, leaving the `.btn` entry intact.

## 3. Admin renderers: class-only previews

- [x] 3.1 Update `ArtworkAdmin.display_image` (`artworks/admin.py`) to emit `class="img-preview img-preview--sm"` with no inline `style=` attribute, keeping the `"-"` fallback.
- [x] 3.2 Update `ArtworkImageInline.display_preview` (`artworks/admin.py`) to emit `class="img-preview"` with no inline `style=` attribute, keeping the `"-"` fallback.

## 4. Docs update

- [x] 4.1 Update `docs/django-unfold-admin.md` section 5 to document `.img-preview` as a CSS class in `static/css/style.css` (base + `--sm` and `--lg` size variants), replacing the JS-injection description, and note that previews must not use inline styles.

## 5. Verification

- [x] 5.1 Confirm no `<img>` in `artworks/admin.py` contains an inline `style=` attribute for previews.
- [x] 5.2 Confirm no `.img-preview` selector remains in `static/js/add_tailwind_styles.js`.
- [x] 5.3 Run Django checks (e.g. `python manage.py check`) to confirm no errors.
- [x] 5.4 Manually verify the Artwork changelist thumbnail and the `ArtworkImageInline` preview render correctly.
