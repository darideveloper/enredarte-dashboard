## ADDED Requirements

### Requirement: Blog Data Models Definition
The system SHALL provide `Post`, `PostTranslation`, and `BlogImage` models adhering to project conventions.

#### Scenario: Post model definition
- **WHEN** the `Post` model is inspected
- **THEN** it inherits from `BaseModel`
- **AND** it defines `banner_image_url`, `author`, and `published_at`
- **AND** it provides a `translated_title()` method and a content-based `__str__()` returning the translated title

#### Scenario: PostTranslation model definition
- **WHEN** the `PostTranslation` model is inspected
- **THEN** it inherits from `SlugBackfillMixin` and `TranslationBase`
- **AND** it defines `post` foreign key, `title`, `description`, `keywords`, and `content`
- **AND** it sets `slug_source = "title"` and `unique_together = [("post", "language")]`
- **AND** `__str__()` returns `f"{self.post} ({self.language})"`

#### Scenario: BlogImage model definition
- **WHEN** the `BlogImage` model is inspected
- **THEN** it inherits from `TimeStampedModel`
- **AND** it defines `name` and `image` (uploading to `blog/images`)
- **AND** `__str__()` returns `self.name`

### Requirement: Blog App Settings Registration and Migrations
The system SHALL register the `blog` app in `INSTALLED_APPS` and maintain clean database migrations.

#### Scenario: App registration and schema migration
- **WHEN** `INSTALLED_APPS` in `project/settings.py` is inspected
- **THEN** `"blog"` is registered
- **AND** `blog/migrations/0001_initial.py` exists and creates the `blog_post`, `blog_posttranslation`, and `blog_blogimage` tables
