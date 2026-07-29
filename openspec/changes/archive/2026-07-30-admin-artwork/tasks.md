## 1. Implementation

- [x] 1.1 Import `Artwork`, `ArtworkTranslation`, `ArtworkImage`, `ArtworkStatus` into `artworks/admin.py`.
- [x] 1.2 Create `ArtworkTranslationInline` extending `StackedInline` and using `TranslationInlineFormSet`. Set `fields = ["language", "title", "description"]`.
- [x] 1.3 Create `ArtworkImageInline` extending `TabularInline`. Configure `ordering_field = "sort_order"`, `hide_ordering_field = True`, and add an image preview method.
- [x] 1.4 Register `ArtworkAdmin` using `@admin.register(Artwork)` extending `ModelAdminUnfoldBase`.
- [x] 1.5 Configure `ArtworkAdmin` fieldsets: Main Attributes, Classification, Pricing & Status, and System Info.
- [x] 1.6 Add inlines `[ArtworkTranslationInline, ArtworkImageInline]` (plus `ArtworkGalleryInline` if applicable) and `sidebar_icon = "palette"`.
- [x] 1.7 Implement `display_title`, `display_image`, `display_price`, and status badge methods on `ArtworkAdmin`.
- [x] 1.8 Implement `get_changeform_initial_data` to auto-populate `sort_order`.

## 2. Verification

- [x] 2.1 Add `ArtworkAdminTestCase` in `artworks/tests.py` testing registration, translation pre-population, inlines, and display methods.
- [x] 2.2 Run `python manage.py test artworks` to verify all tests pass.
