## Why

The `Artist` and `ArtistTranslation` database models are already created in `artworks/models.py`, but they are not registered in the Django Admin site (`artworks/admin.py` is empty). To enable managing artists and their multi-language biography content (Spanish & English) directly from the admin dashboard, the `Artist` model must be registered with inline support for `ArtistTranslation`.

## What Changes

- Register `Artist` model in `artworks/admin.py` using `ModelAdminUnfoldBase`.
- Add `ArtistTranslationInline` using `StackedInline` to allow editing Spanish and English translations directly on the Artist edit screen.
- Localize all admin list display table headers, action labels, search fields, and inline titles into Spanish without modifying any model code in `models.py`.

## Capabilities

### New Capabilities
- `artist-admin`: Management of Artists and multi-language ArtistTranslations (Spanish and English) directly inside the Django Unfold admin panel.

### Modified Capabilities
<!-- None -->

## Impact

- `artworks/admin.py`: Will register `Artist` and `ArtistTranslationInline`.
- Django Admin interface: A new "Artistas" section will appear in the dashboard under the red Unfold theme.
- No changes to `artworks/models.py` or database migrations.
