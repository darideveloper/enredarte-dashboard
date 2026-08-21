## Why

The system needs a data layer to support blog articles and media assets. Following the project's translation and model architecture, we define the `Post`, `PostTranslation`, and `BlogImage` models to store multi-language blog posts and images, while keeping the scope strictly bounded to the model definitions, configuration, and migrations.

## What Changes

- Register `"blog"` in `INSTALLED_APPS` within `project/settings.py`.
- Define `Post` model in `blog/models.py` inheriting from `BaseModel` with shared fields: `banner_image_url`, `author`, and `published_at`.
- Define `PostTranslation` model in `blog/models.py` inheriting from `SlugBackfillMixin` and `TranslationBase` with language-specific fields: `title`, `description`, `keywords`, and `content`.
- Define `BlogImage` model in `blog/models.py` inheriting from `TimeStampedModel` for uploading and managing blog image assets.
- Generate and execute Django initial migrations for the `blog` app.

## Capabilities

### New Capabilities
- `blog-models`: Data models (`Post`, `PostTranslation`, `BlogImage`) and database schema for the blog module.

### Modified Capabilities
<!-- None -->

## Impact

- `project/settings.py`: Adds `"blog"` to `INSTALLED_APPS`.
- `blog/models.py`: Model declarations.
- Database: Creates new database tables `blog_post`, `blog_posttranslation`, and `blog_blogimage`.
