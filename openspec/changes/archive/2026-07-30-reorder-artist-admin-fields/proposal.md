## Why

The `Artist` model in Django admin currently displays the `slug` field at the very top, before the `name` field, because `Artist` inherits from `Person` which inherits from `BaseModel` (where `slug` is defined). This makes the layout unintuitive, especially since the `slug` is configured to auto-populate from `name`.

## What Changes

- Reorder fields in `ArtistAdmin` to place `slug` logically after `name`.
- Use Django Admin `fieldsets` (supported by Unfold) to group information logically into distinct sections (e.g., Personal Info, Contact & Media, System Status).

## Capabilities

### New Capabilities
None.

### Modified Capabilities
- `artist-admin`: The administrative layout for the Artist form is being reorganized.

## Impact

- **Affected code**: `artworks/admin.py` -> `ArtistAdmin`
- **UI Impact**: The Django Admin add/edit form for Artist will be reorganized to be more user-friendly.
