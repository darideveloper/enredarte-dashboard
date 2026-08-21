## 1. Implementation

- [x] 1.1 Import `Gallery`, `GalleryTranslation`, `ArtworkGallery` into `artworks/admin.py`. Also import `TabularInline` from `unfold.admin`.
- [x] 1.2 Create `GalleryTranslationInline` extending `StackedInline` and using `TranslationInlineFormSet`. Set `max_num = len(settings.LANGUAGES)` and override `get_extra` to match existing translation inlines.
- [x] 1.3 Create `ArtworkGalleryInline` extending `TabularInline`. Set `model = ArtworkGallery`, `fields = ["artwork"]`, `ordering_field = "sort_order"`, `hide_ordering_field = True`, and `extra = 0`.
- [x] 1.4 Register `GalleryAdmin` using `@admin.register(Gallery)` extending `ModelAdminUnfoldBase`.
- [x] 1.5 Configure `GalleryAdmin` with `inlines = [GalleryTranslationInline, ArtworkGalleryInline]`, `sidebar_icon = "storefront"`, `search_fields`, `list_filter`, and `fieldsets`.
- [x] 1.6 Implement `display_name` on `GalleryAdmin` to show the Spanish name (or fallback).
- [x] 1.7 Implement `get_changeform_initial_data` to auto-populate `sort_order` like other models.

## 2. Verification

- [x] 2.1 Add `GalleryAdminTestCase` in `artworks/tests.py` testing registration, translation pre-population, and `sort_order` initial data.
- [x] 2.2 Add tests to ensure `ArtworkGalleryInline` is present in `GalleryAdmin`'s inlines.
- [x] 2.3 Run `python manage.py test artworks` to verify all tests pass.
