## Why

In the Django admin (`admin/artworks/gallery/<id>/change/`), trying to mark a gallery as primary fails with the form error `No se cumple la restricción "unique_primary_gallery"` instead of auto-unmarking the existing primary gallery. The `is_primary` flag can only be changed through non-admin ORM writes, which makes the flag effectively unusable from the admin — the exact place it is meant to be managed.

Root cause: Django's `ModelForm.full_clean()` calls `validate_constraints()` before `Gallery.save()` runs. Because an existing primary gallery is already in the DB, constraint validation fails and `save()` — where the auto-unflag lives — is never reached.

## What Changes

- Add an admin-level form (`GalleryAdminForm`) whose `clean()` unflags any other primary gallery **before** constraint validation, whenever `is_primary=True` is submitted.
- Wire the form into `GalleryAdmin` so the admin change/add form uses it.
- Keep the `Gallery.save()` override as-is: it still covers plain ORM writes (e.g. `objects.create()`), fixtures, and the API.
- Keep the database-level `unique_primary_gallery` constraint untouched: it remains the backstop for direct DB writes that bypass the ORM (`bulk_create`, `update()`).
- Add regression tests that reproduce the reported bug by driving the admin form path (change and add forms), asserting that validation passes and the previous primary gallery is unmarked.

## Capabilities

### New Capabilities

_None. No new standalone behavior; the fix adjusts an existing capability's requirement._

### Modified Capabilities

- `gallery-primary-flag`: The "Only one primary gallery exists" requirement currently only guarantees auto-unflag "when a gallery is saved as primary through the ORM". This change extends it so that **any** form-based save (including the Django admin change/add forms) auto-unflags the previous primary instead of failing validation. The DB constraint rejection backstop remains unchanged.

## Impact

- `artworks/admin.py` — add `GalleryAdminForm` (or local equivalent) and set `form = GalleryAdminForm` on `GalleryAdmin`.
- `artworks/models.py` — unchanged; existing `Gallery.save()` override stays.
- `artworks/tests.py` — add regression test for the admin-form path.
- `openspec/specs/gallery-primary-flag/spec.md` — add a scenario and sharpen the requirement wording.
- No migrations, no DB schema changes, no API changes.