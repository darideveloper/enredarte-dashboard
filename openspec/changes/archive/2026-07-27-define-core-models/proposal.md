## Why

The project has an empty `artworks` app with no models defined. The core domain entities — artists, curators, galleries, artworks, and taxonomy — need to be modeled before any API or admin functionality can be built. The SSG frontend needs a well-structured, bilingual data backbone.

## What Changes

- Create `core` app with reusable abstract base models (`TimeStampedModel`, `BaseModel`, `TranslationBase`)
- Create `artworks` app models: `Artist`, `ArtCurator`, `Gallery`, `Artwork`, `ArtworkImage`, `ArtworkGallery` (M2M through)
- Create taxonomy models: `Category`, `Medium`, `Surface` — each with translations
- Add `LANGUAGES` setting with `es` and `en`
- Translatable text fields (title, description, bio) move to per-model `Translation` tables; non-translatable fields (Artist/ArtCurator name) stay on the main model; Gallery name is translated
- `Person` abstract base model for shared person fields (name, email, website, photo)

## Capabilities

### New Capabilities
- `core-models`: Abstract base classes and shared infrastructure (`TimeStampedModel`, `BaseModel`, `TranslationBase`, `Person`)
- `artwork-catalog`: Artwork, Artist, ArtCurator, Gallery models with full bilingual translation support
- `artwork-taxonomy`: Category, Medium, Surface classification models with translations
- `artwork-media`: ArtworkImage model for multi-image support with primary image and alt text

### Modified Capabilities
- *(none — no existing specs affected)*

## Impact

- New Django app: `artworks/` (models)
- New Django app: `core/` (abstract base models, shared utilities)
- `project/settings.py`: add `core` to `INSTALLED_APPS`, add `LANGUAGES`
- New database tables for all models and translation tables
- Future API endpoints, admin config, and SSG integration will build on this foundation
