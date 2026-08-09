## 1. Refactor translation inlines into a shared base

- [x] 1.1 Add a `clean()` override to `TranslationInlineFormSet` in `artworks/admin.py` that raises `ValidationError` unless exactly `len(settings.LANGUAGES)` non-empty, non-deleted translation rows are present (a row is non-empty when any translated field other than `language` is filled)
- [x] 1.2 Add `TranslationInline(StackedInline)` base class in `artworks/admin.py` (after `TranslationInlineFormSet`) with `formset = TranslationInlineFormSet`, `verbose_name = "Traducción"`, `verbose_name_plural = "Traducciones (Español / Inglés)"`, `can_delete = False`, `min_num = max_num = len(settings.LANGUAGES)`, and the existing `get_extra` logic
- [x] 1.3 Convert `ArtistTranslationInline` and `ArtCuratorTranslationInline` to subclass `TranslationInline`, keeping only `model` and `fields = ["language", "bio"]`
- [x] 1.4 Convert `DisciplineTranslationInline`, `TechniqueTranslationInline`, `ThemeTranslationInline`, `FormatTranslationInline`, `ScaleTranslationInline`, `LocationTranslationInline` to subclass `TranslationInline` with `fields = ["language", "name"]`
- [x] 1.5 Convert `GalleryTranslationInline` to subclass `TranslationInline` with `fields = ["language", "name", "description"]`
- [x] 1.6 Convert `ArtworkTranslationInline` to subclass `TranslationInline` with `fields = ["language", "title", "description"]`

## 2. Verify

- [x] 2.1 Load Django and confirm every admin change form (Artist, ArtCurator, Discipline, Technique, Theme, Format, Scale, Gallery, Location, Artwork) renders without errors and no translation inline shows a delete control
- [x] 2.2 Confirm saving a parent with both languages filled succeeds, and saving with only one language filled is rejected with a validation error
- [x] 2.3 Confirm existing parents with 0 or 1 translations are blocked on save until both `es` and `en` are filled
- [x] 2.4 Confirm saving a new parent with the translation inline left completely untouched is rejected (no parent with zero translations can be persisted)
