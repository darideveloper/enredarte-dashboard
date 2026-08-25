## 1. CSS & Documentation Updates

- [x] 1.1 Add `.img-preview--banner` and `.img-preview--form` rules to `static/css/style.css` and verify stylesheet definition
- [x] 1.2 Update `docs/django-unfold-admin.md` to document the new preview modifier classes

## 2. Admin Renderers Refactoring

- [x] 2.1 Update `PostAdmin.display_banner` and `PostAdmin.display_banner_preview` in `blog/admin.py` to use `.img-preview` classes without inline styles
- [x] 2.2 Update `BlogImageAdmin.display_preview` and `BlogImageAdmin.display_preview_large` in `blog/admin.py` to use `.img-preview` classes without inline styles

## 3. Test Suite & Verification

- [x] 3.1 Add unit tests in `blog/tests.py` testing image preview HTML classes and asserting no inline `style=` attributes
- [x] 3.2 Run test suite across `blog` and validate change with `openspec validate --changes standardize-blog-image-previews`
