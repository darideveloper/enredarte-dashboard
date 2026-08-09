## Why

Unfold's file/image upload widgets render a fake disabled `<input type="text">` whose width is driven only by its intrinsic `size`, so the "Seleccionar archivo para subir" label is clipped/truncated and not fully visible. The fix is a tiny CSS rule, but it must be applied consistently to every file input (change forms and inlines) in one place.

## What Changes

- Add a single scoped CSS rule to `static/css/style.css` that makes the fake filename text input fill the widget width so the label is fully visible. The rule turns the widget's wrapping label into a flex container (`display: flex`), which activates the input's existing `grow`/`min-w-0` classes — chosen over `width: 100%` because the latter regresses the small inline widget.
- The selector targets `label.grow.relative`, which exists only in Unfold's `clearable_file_input.html` and `clearable_file_input_small.html` templates, so both the regular (image preview) widget and the small inline widget are covered.
- No Python, template, or settings changes. No new dependencies.

## Capabilities

### New Capabilities
- `admin-file-input`: The Django admin file/image upload widgets render their filename text input at full widget width so the placeholder/label text is fully visible in both change forms and inline forms.

### Modified Capabilities
<!-- No existing spec-level behavior changes. -->

## Impact

- `static/css/style.css`: new rules appended (file already loaded globally on all admin pages via `project/templates/admin/base.html`).
- Applies to all `ImageField`/`FileField` inputs in every `ModelAdminUnfoldBase`-derived admin and every Unfold inline (`TabularInline`/`StackedInline`) — currently the `photo`/`image`/`logo` fields on Artist, ArtCurator, Artwork, Gallery models.
- No API, database, or dependency impact. Visually scoped to the file upload widgets only.
