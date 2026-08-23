## MODIFIED Requirements

### Requirement: Blog Data Models Definition
The system SHALL provide `Post`, `PostTranslation`, and `BlogImage` models adhering to project conventions. The `Post` model SHALL NOT define a `sort_order` field.

#### Scenario: Post model definition
- **WHEN** the `Post` model is inspected
- **THEN** it inherits from `BaseModel`
- **AND** it defines `banner_image`, `author`, and `published_at`
- **AND** it SHALL NOT define a `sort_order` field
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
