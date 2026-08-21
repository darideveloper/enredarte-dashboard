## Context

The `blog` app exists as a package skeleton. We need to introduce the database model layer to support blog posts and images adhering to project conventions (`docs/django-model-definitions.md`, `AGENTS.md`). Specifically, the blog posts must support Spanish and English translations using our standard `BaseModel` + `TranslationBase` + `SlugBackfillMixin` pattern.

## Goals / Non-Goals

**Goals:**
- Add `"blog"` to `INSTALLED_APPS` in `project/settings.py`.
- Define `Post` (inherits `BaseModel`), `PostTranslation` (inherits `SlugBackfillMixin`, `TranslationBase`), and `BlogImage` (inherits `TimeStampedModel`) in `blog/models.py`.
- Enforce strict `AGENTS.md` conventions: Spanish `verbose_name` on all fields, `help_text` on non-obvious fields, `Meta.verbose_name` / `verbose_name_plural`, content-based `__str__`.
- Generate and apply initial database migrations for `blog`.

**Non-Goals:**
- Django Admin interface and inlines (deferred to `blog-admin` proposal).
- REST API serializers and endpoints (deferred to `blog-apis` proposal).
- Test fixtures and seed content (deferred to `blog-fixtures-tests` proposal).

## Decisions

### 1. Translation Architecture
- **Decision**: Separate shared attributes (`banner_image_url`, `author`, `published_at`, `is_active`, `sort_order`) on `Post`, and translated attributes (`title`, `description`, `keywords`, `content`) on `PostTranslation`.
- **Rationale**: Matches the standard pattern established in `artworks` (`Artwork` + `ArtworkTranslation`), enabling single-screen multilingual editing in admin and multi-language REST responses.

### 2. Auto-slug Generation via `SlugBackfillMixin`
- **Decision**: Use `SlugBackfillMixin` with `slug_source = "title"` on `PostTranslation`.
- **Rationale**: When the Spanish translation is saved, `unique_slugify` auto-populates `Post.slug` seamlessly.

### 3. Media Upload via `BlogImage`
- **Decision**: Define a dedicated `BlogImage` model with `upload_to="blog/images"`.
- **Rationale**: Allows content creators to upload images that can be embedded into post banners or markdown content.

## Risks / Trade-offs

- **[Risk]** Database schema changes: requires migration.
  - **Mitigation**: Generated clean migration `0001_initial.py` applied via `manage.py migrate blog`.
