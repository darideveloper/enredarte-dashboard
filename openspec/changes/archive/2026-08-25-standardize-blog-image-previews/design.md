## Context

See `proposal.md` for motivation. Currently, `blog/admin.py` defines 4 image preview methods (`PostAdmin.display_banner`, `PostAdmin.display_banner_preview`, `BlogImageAdmin.display_preview`, and `BlogImageAdmin.display_preview_large`) using inline `style=` attributes. This contrasts with `artworks/admin.py`, where all image previews use pure CSS classes defined in `static/css/style.css` without inline styles.

## Goals / Non-Goals

**Goals:**
- Add `.img-preview--banner` and `.img-preview--form` CSS classes to `static/css/style.css`.
- Update all image preview renderers in `blog/admin.py` to emit CSS classes with zero inline `style=` attributes.
- Update `docs/django-unfold-admin.md` with the new modifier class documentation.
- Add unit tests in `blog/tests.py` testing each image preview renderer's HTML output.

**Non-Goals:**
- Modifying backend models or migrations (image URLs and uploads remain unchanged).
- Modifying REST API endpoints or serializers.

## Decisions

### 1. CSS Rule Organization in `static/css/style.css`
- **Decision**: Extend the image preview section in `static/css/style.css` with:
  ```css
  .img-preview--banner {
      max-height: 180px;
      max-width: 100%;
      border-radius: 8px;
      object-fit: cover;
  }

  .img-preview--form {
      max-height: 240px;
      max-width: 100%;
      border-radius: 8px;
      object-fit: cover;
  }
  ```
- **Rationale**: Keeps all preview dimensions, aspect ratio controls, and borders in the central CSS stylesheet, preserving visual appearance without inline styles.

### 2. Standardized HTML Output in `blog/admin.py`
- **Decision**: Update the four methods:
  - `PostAdmin.display_banner`: `format_html('<img src="{}" class="img-preview img-preview--sm" />', obj.banner_image.url)`
  - `PostAdmin.display_banner_preview`: `format_html('<img src="{}" class="img-preview--banner" />', obj.banner_image.url)`
  - `BlogImageAdmin.display_preview`: `format_html('<img src="{}" class="img-preview img-preview--sm" />', obj.image.url)`
  - `BlogImageAdmin.display_preview_large`: `format_html('<img src="{}" class="img-preview--form" />', obj.image.url)`
- **Rationale**: Exactly aligns with `artworks/admin.py` (`ArtworkAdmin.display_image` and `ArtworkImageInline.display_preview`).

### 3. Test Coverage & Assertions
- **Decision**: Add dedicated test methods in `blog/tests.py` asserting `assertIn('class="img-preview..."', html)` and `assertNotIn("style=", html)` for both presence and fallback states.
- **Rationale**: Prevents future regressions and mirrors the test suite in `artworks/tests.py`.

## Risks / Trade-offs

- **[Risk] Browser CSS Cache**: Clients viewing the admin might need a cache refresh if CSS is cached.
  - **Mitigation**: Unfold loads static files via standard Django static tag which respects cache busting in production.
