## Why

When editing or creating an `Artist` in Django Admin, `ArtistTranslationInline` currently presents two issues:
1. Two blank inline forms are added on new creation without defaulting the language selection (one form should default to Spanish `es` and the other to English `en`).
2. When editing an existing artist that already has translation records saved, Django Admin appends 2 extra blank translation forms instead of only displaying the existing translations.

Fixing these behaviors improves administrator productivity and prevents unwanted empty translation rows or manual language selection errors.

## What Changes

- Customize `ArtistTranslationInline` in `artworks/admin.py`:
  - Dynamically set `extra = 0` when editing an existing artist that already has translations, or calculate `extra` to not exceed 2 total translations.
  - Set `max_num = 2` to prevent adding more than the supported languages (Spanish and English).
  - Pre-populate default language initial values (`es` for the first inline form, `en` for the second) when creating a new artist.

## Capabilities

### New Capabilities
<!-- None -->

### Modified Capabilities
- `artist-admin`: Updated inline translation requirements to default languages (`es` and `en`) and avoid appending extra blank forms when editing existing artist records.

## Impact

- `artworks/admin.py`: Modifies `ArtistTranslationInline` and `ArtistAdmin`.
- `artworks/tests.py`: Updated test suite to verify inline pre-population and extra form behavior.
- Zero changes to `artworks/models.py`.
