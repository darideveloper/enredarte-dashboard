## Why

The admin exposes 10 near-identical translation inlines (Artist, ArtCurator, Discipline, Technique, Theme, Format, Scale, Gallery, Location, Artwork) that allow arbitrary creation and deletion of language rows. Nothing guarantees a parent ends up with exactly two translations (Spanish + English): a user can delete a row or save with one language left blank, leaving incomplete content. The inline classes are also ~90% duplicated boilerplate.

## What Changes

- Add a shared base inline class (`TranslationInline`) carrying the common behavior for all 10 translation inlines: `TranslationInlineFormSet` (with a `clean()` override requiring exactly `len(settings.LANGUAGES)` non-empty, non-deleted rows), `can_delete = False`, `min_num = max_num = len(settings.LANGUAGES)`, `verbose_name_plural = "Traducciones (Español / Inglés)"`, and the existing `get_extra` logic.
- Collapse each of the 10 translation inline classes to subclass the base, keeping only `model` and `fields`.
- Enforce that every translated parent always has exactly 2 translation rows: no row can be deleted, and saving fails unless both Spanish and English rows are present and will be persisted — including when the inline is left untouched, and on legacy data already missing a language.

## Capabilities

### New Capabilities
- `translation-inline-management`: Behavior of the translation inline editors in the Django admin — always exactly two rows (es + en), no deletion, enforced on save via `can_delete`/`min_num`/`max_num`, backed by a single shared base inline class.

### Modified Capabilities
<!-- No existing spec's requirements change; the translation inline behavior is not currently specified anywhere. -->

## Impact

- `artworks/admin.py`: the 10 translation inline classes and their definitions; adds the `TranslationInline` base class.
- Runtime behavior of the Django admin change forms for Artist, ArtCurator, Discipline, Technique, Theme, Format, Scale, Gallery, Location, Artwork.
- Existing incomplete data (parents with 0 or 1 translations) will block saving until both languages are filled.
- No model, migration, API, or frontend changes.
