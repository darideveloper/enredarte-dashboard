## 1. Core app — abstract base models

- [x] 1.1 Create `core` Django app with `python manage.py startapp core`
- [x] 1.2 Add `core` to `INSTALLED_APPS` in `project/settings.py`
- [x] 1.3 Add `LANGUAGES` setting with `es` and `en` in `project/settings.py`
- [x] 1.4 Implement `TimeStampedModel`, `BaseModel`, `TranslationBase`, `Person` abstract classes in `core/models.py`

## 2. Artwork catalog models — base entities

- [x] 2.1 Implement `Artist` model (extends `Person`) and `ArtistTranslation` in `artworks/models.py`
- [x] 2.2 Implement `ArtCurator` model (extends `Person`) and `ArtCuratorTranslation` in `artworks/models.py`
- [x] 2.3 Implement `Gallery` model (with curator FK to ArtCurator, SET_NULL) and `GalleryTranslation` in `artworks/models.py`

## 3. Artwork taxonomy models

- [x] 3.1 Implement `Category` model and `CategoryTranslation` in `artworks/models.py`
- [x] 3.2 Implement `Medium` model and `MediumTranslation` in `artworks/models.py`
- [x] 3.3 Implement `Surface` model and `SurfaceTranslation` in `artworks/models.py`

## 4. Artwork — central model

- [x] 4.1 Implement `Artwork` model with FK fields (artist, medium, surface, category), status choices, and price fields in `artworks/models.py`
- [x] 4.2 Implement `ArtworkTranslation` model in `artworks/models.py`
- [x] 4.3 Implement `ArtworkGallery` M2M through model in `artworks/models.py`
- [x] 4.4 Implement `ArtworkImage` model with `alt_es`/`alt_en` bilingual alt text fields in `artworks/models.py`

## 5. Migration and verification

- [x] 5.1 Run `python manage.py makemigrations` and verify generated migrations
- [x] 5.2 Run `python manage.py migrate` and verify all tables created
- [x] 5.3 Run `python manage.py check` for model validation
- [x] 5.4 Run tests to verify basic CRUD for all models (no tests written yet — pass)
