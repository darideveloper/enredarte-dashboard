## 1. Inline & Admin Definition

- [x] 1.1 Create `ArtistTranslationInline` class in `artworks/admin.py` using `unfold.contrib.inlines.StackedInline` with Spanish verbose titles and `extra = 2`.
- [x] 1.2 Create `ArtistAdmin` class in `artworks/admin.py` extending `ModelAdminUnfoldBase`.
- [x] 1.3 Configure list display table headers in Spanish, filters for `is_active`, search fields, and prepopulated slug field.

## 2. Model Registration & Verification

- [x] 2.1 Register `Artist` model with `ArtistAdmin` in `artworks/admin.py`.
- [x] 2.2 Verify admin setup using Django system checks / dry-run test.
