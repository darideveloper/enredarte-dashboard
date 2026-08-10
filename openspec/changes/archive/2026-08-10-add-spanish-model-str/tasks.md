## 1. Model mixin

- [x] 1.1 Add abstract `TranslatableName` mixin to `core/models.py` with `translated_name(language="es")` (es → any translation → slug) and `__str__`

## 2. Content model strings

- [x] 2.1 Change `Location`, `Gallery`, `Discipline`, `Technique`, `Theme`, `Format`, `Scale` to inherit `TranslatableName` (replacing `BaseModel`) in `artworks/models.py`
- [x] 2.2 Add `Artwork.translated_title()` and `__str__` (es → any translation → slug) to `artworks/models.py`

## 3. Translation row strings

- [x] 3.1 Add `__str__` returning `f"{self.<parent>} ({self.language})"` to all 10 translation models: `ArtistTranslation`, `LocationTranslation`, `ArtCuratorTranslation`, `GalleryTranslation`, `DisciplineTranslation`, `TechniqueTranslation`, `ThemeTranslation`, `FormatTranslation`, `ScaleTranslation`, `ArtworkTranslation`

## 4. Join model strings

- [x] 4.1 Add `__str__` to `ArtistSocialLink`: `f"{self.get_platform_display()} — {self.artist}"`
- [x] 4.2 Add `__str__` to `ArtworkGallery`: `f"{self.artwork} en {self.gallery}"`
- [x] 4.3 Add `__str__` to `ArtworkImage`: `self.alt_es or f"Imagen de {self.artwork}"`

## 5. Tests

- [x] 5.1 Add `ModelStrTestCase` in `artworks/tests.py` covering: taxonomy Spanish preference, non-Spanish fallback, slug fallback, artwork title preference/fallback, translation-row format, and the three join-model strings

## 6. Documentation

- [x] 6.1 Update `docs/django-i18n-es-admin.md` Step 2 with the translated-model `__str__` convention (`TranslatableName` / `translated_name()` Spanish-first lookup) alongside the existing direct-`name` example

## 7. Verification

- [x] 7.1 Run `python manage.py test artworks` and confirm all tests (new + existing) pass
