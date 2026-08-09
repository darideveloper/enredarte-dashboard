## 1. Apply the CSS fix

- [x] 1.1 Append the file-input width rule to `static/css/style.css`:
      `label.grow.relative { display: flex; }` (activates the input's existing `grow`/`min-w-0` classes; `width: 100%` was rejected as it regresses the small inline widget)
- [x] 1.2 Verify the rule sits in its own clearly-labeled block and does not conflict with existing `.editor-preview` rules

## 2. Verify in the browser

- [x] 2.1 Load an admin change form with an `ImageField` (e.g. Artist photo, Gallery logo, Artwork image) and confirm the "Seleccionar archivo para subir" label is fully visible at widget width
- [x] 2.2 Load the only inline that renders a file/image field (`ArtworkImageInline`) and confirm the small file widget label is fully visible
- [x] 2.3 Confirm regular text inputs and readonly fields elsewhere in the admin are unaffected

## 3. Update documentation

- [x] 3.1 Update `docs/django-unfold-admin.md` so the "Markdown Preview Styling (`static/css/style.css`)" section documents the new file-input width rule (or add a short subsection for it)
- [x] 3.2 Update `docs/django-project-setup.md` if it describes the contents/purpose of `static/css/style.css` (reviewed — it only instructs creating an empty file, so no update needed)
- [x] 3.3 Re-run `collectstatic` (or the equivalent used by the project) and confirm `staticfiles/css/style.css` contains the new rule (ran `collectstatic` → 201 files uploaded to the S3/CDN bucket; `enredarte/static/css/style.css` now contains the rule)
