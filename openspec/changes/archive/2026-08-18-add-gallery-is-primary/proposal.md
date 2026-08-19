## Why

The frontend needs to identify a single "main" gallery from the collection to feature as the hero/prominent gallery (e.g., homepage). Today `Gallery` has no flag to mark it, so the frontend cannot distinguish the main gallery from the rest. This is the same need already solved for `Artwork` (`is_highlighted`) and `ArtworkImage` (`is_primary`).

## What Changes

- Add an `is_primary` boolean field to the `Gallery` model (verbose_name "Galería principal"), defaulting to `False`, mirroring the existing `ArtworkImage.is_primary` precedent.
- Enforce a **single primary gallery** (option A semantics): uniqueness is guaranteed at the **database level** via a conditional unique constraint on `is_primary`, so at most one active gallery is primary across the whole backend. The ORM `save()` also auto-un-marks the previous primary.
- Expose `is_primary` in the `GallerySerializer` so the frontend can read it from `GET /apis/artworks/galleries/` (list and detail).
- Surface `is_primary` in `GalleryAdmin`: add to the "Información básica" fieldset, `list_display`, and `list_filter` so admins can flag, view, and find the main gallery.
- Generate a Django migration for the new field.
- Add tests covering the model default, the flag behavior, single-primary enforcement, serializer output, and admin exposure.

## Capabilities

### New Capabilities

- `gallery-primary-flag`: The `Gallery.is_primary` boolean field, its single-primary enforcement, and its exposure through the API serializer and Django Admin.

### Modified Capabilities

- `artworks-rest-api`: The Gallery endpoint entries SHALL now also include the `is_primary` field.
- `gallery-admin`: The Gallery admin edit form and changelist SHALL expose the `is_primary` field.

## Impact

- `artworks/models.py` — new `Gallery.is_primary` field + `save()` enforcement logic.
- `artworks/migrations/` — new migration adding the field.
- `artworks/serializers.py` — `GallerySerializer` fields list gains `is_primary`.
- `artworks/admin.py` — `GalleryAdmin` fieldset, `list_display`, `list_filter`.
- `artworks/tests.py` — new tests.
- No API breaking changes (additive field only).
