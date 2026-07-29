## 1. Implementation

- [x] 1.1 Rename `ArtistTranslationFormSet` to `TranslationInlineFormSet` in `artworks/admin.py` and update `ArtistTranslationInline` to use it.
- [x] 1.2 Import `ArtCurator`, `ArtCuratorTranslation` into `artworks/admin.py`.
- [x] 1.3 Create `ArtCuratorTranslationInline` extending `StackedInline` and using `TranslationInlineFormSet`. Set `max_num = len(settings.LANGUAGES)` and override `get_extra` to calculate remaining forms dynamically.
- [x] 1.4 Register `ArtCuratorAdmin` using `@admin.register(ArtCurator)` extending `ModelAdminUnfoldBase`.
- [x] 1.5 Configure `ArtCuratorAdmin` layout with `inlines`, `prepopulated_fields`, `search_fields`, `list_filter`, and `fieldsets` matching the Artist structure (omitting birth/death year).
- [x] 1.6 Implement `get_changeform_initial_data` in `ArtCuratorAdmin` to auto-fill `sort_order` with `max(sort_order) + 1` (default 1).

## 2. Verification

- [x] 2.1 Add unit tests in `artworks/tests.py` testing `ArtCuratorAdmin` registration, form layout, translations pre-population, and `sort_order` auto-fill.
- [x] 2.2 Run `python manage.py test artworks` to verify tests pass.
