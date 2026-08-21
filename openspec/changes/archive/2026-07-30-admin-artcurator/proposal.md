## Why

The `ArtCurator` model was recently added to the `artworks` app but currently lacks an interface in Django Admin. Without it, administrators cannot add, edit, or manage curators and their bilingual biographies.

## What Changes

- Register the `ArtCurator` model in Django Admin via `artworks/admin.py`.
- Apply a clean, Unfold-styled layout using `ModelAdminUnfoldBase`.
- Add an inline section for `ArtCuratorTranslation` to manage Spanish/English bios on the same page.
- Pre-populate translation languages on creation.
- Auto-fill `sort_order` for new curators with `max(sort_order) + 1` (scoped only to this model for now).

## Capabilities

### New Capabilities
- `art-curator-admin`: Add, view, edit, and list Art Curators with inline bilingual bios.

### Modified Capabilities
- `artist-admin`: We will rename `ArtistTranslationFormSet` to a generic name so both `Artist` and `ArtCurator` can share the language pre-population logic without duplicating code.

## Impact

- **Affected code**: `artworks/admin.py`, `artworks/tests.py`
- **UI Impact**: A new "Curators" (or similar icon) section will appear in the Django Admin sidebar.
