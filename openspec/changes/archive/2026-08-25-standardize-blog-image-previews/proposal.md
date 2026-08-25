## Why

Image preview renderers in `blog/admin.py` currently emit inline `style=` attributes (`style="height: 40px; width: 40px; object-fit: cover; border-radius: 6px;"`, etc.), which duplicates styling, bypasses the CSS stylesheet, and violates the project's standardized preview conventions established in `docs/django-unfold-admin.md` and spec `admin-image-preview`.

## What Changes

- Define `.img-preview--banner` and `.img-preview--form` classes in `static/css/style.css` for changeview form previews.
- Update `PostAdmin.display_banner` in `blog/admin.py` to emit `class="img-preview img-preview--sm"` without inline styles.
- Update `PostAdmin.display_banner_preview` in `blog/admin.py` to emit `class="img-preview--banner"` without inline styles.
- Update `BlogImageAdmin.display_preview` in `blog/admin.py` to emit `class="img-preview img-preview--sm"` without inline styles.
- Update `BlogImageAdmin.display_preview_large` in `blog/admin.py` to emit `class="img-preview--form"` without inline styles.
- Update `docs/django-unfold-admin.md` to document the new `.img-preview--banner` and `.img-preview--form` modifier classes.
- Add unit tests in `blog/tests.py` verifying that all four image renderers emit the appropriate CSS classes and zero inline `style=` attributes.
- Update `admin-image-preview` and `blog-admin` specifications.

## Capabilities

### New Capabilities

None — this is a frontend styling standardization and refactor.

### Modified Capabilities

- `admin-image-preview`: Extends the image preview specification to cover `.img-preview--banner` and `.img-preview--form` variants and enforce that all admin preview renderers across all apps omit inline `style=` attributes.
- `blog-admin`: Specifies that `PostAdmin` and `BlogImageAdmin` render image previews using `.img-preview` classes with no inline styles.

## Impact

- **Code**: `static/css/style.css`, `blog/admin.py`, `blog/tests.py`.
- **Docs**: `docs/django-unfold-admin.md`.
- **Database / API**: None (purely admin UI presentation).
