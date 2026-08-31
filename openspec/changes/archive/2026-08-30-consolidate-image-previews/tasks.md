# Tasks: Consolidate Image Previews

## 1. Blog Admin Cleanup

- [x] 1.1 Remove `display_banner_preview` from `PostAdmin.readonly_fields` and from the "Información principal" fieldset in `blog/admin.py`
- [x] 1.2 Delete the `PostAdmin.display_banner_preview` method in `blog/admin.py`
- [x] 1.3 Remove `display_preview_large` from `BlogImageAdmin.readonly_fields` and from the "Información de la imagen" fieldset in `blog/admin.py`
- [x] 1.4 Delete the `BlogImageAdmin.display_preview_large` method in `blog/admin.py`
- [x] 1.5 Verify `PostAdmin.display_banner` and `BlogImageAdmin.display_preview` (list-view thumbnails) remain untouched

## 2. Artwork Inline Cleanup

- [x] 2.1 Remove `display_preview` from `ArtworkImageInline.fields` in `artworks/admin.py`
- [x] 2.2 Remove `display_preview` from `ArtworkImageInline.readonly_fields` in `artworks/admin.py`
- [x] 2.3 Delete the `ArtworkImageInline.display_preview` method in `artworks/admin.py`
- [x] 2.4 Verify `ArtworkAdmin.display_image` (list-view thumbnail) remains untouched

## 3. CSS Cleanup

- [x] 3.1 Remove `.img-preview--banner` rule from `static/css/style.css`
- [x] 3.2 Remove `.img-preview--form` rule from `static/css/style.css`
- [x] 3.3 Verify `.img-preview`, `.img-preview--sm`, and `.img-preview--lg` remain in `static/css/style.css`

## 4. Tests

- [x] 4.1 Delete `test_post_admin_display_banner_preview` from `blog/tests.py`
- [x] 4.2 Delete `test_blog_image_admin_display_preview_large` from `blog/tests.py`
- [x] 4.3 Add a regression test rendering the Post change form asserting it contains no `img-preview--banner` markup
- [x] 4.4 Add a regression test rendering the BlogImage change form asserting it contains no `img-preview--form` markup
- [x] 4.5 Delete `test_artwork_display_preview_class_and_no_inline_style` and `test_artwork_display_preview_fallback_empty` from `artworks/tests.py`
- [x] 4.6 Run the blog and artworks test suites to confirm green

## 5. Documentation

- [x] 5.1 Update the `.img-preview` section in `docs/django-unfold-admin.md` to drop `--banner`/`--form` classes and the `ArtworkImageInline.display_preview` example, and adjust the usage paragraph (form previews now come from Unfold's native widget)
- [x] 5.2 Confirm `docs/django-image-copy-link.md` needs no changes (copy-button feature is unaffected)

## 6. Verification

- [x] 6.1 Run `python manage.py check` to confirm the admin config is valid
- [x] 6.2 Visually verify the Post and BlogImage change forms show a single image preview (Unfold widget) for existing records
- [x] 6.3 Confirm list views still render thumbnails unchanged