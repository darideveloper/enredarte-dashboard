## ADDED Requirements

### Requirement: Blog seed fixtures exist and load through seed_loaddata
The system SHALL ship seed fixtures for the `blog` app under `blog/fixtures/blog/seed/`, one JSON file per model (`00_Post.json`, `01_PostTranslation.json`, `02_BlogImage.json`), with explicit PKs, explicit timestamps, and explicit slugs, so that `seed_loaddata` populates blog tables on a fresh database that already ran `base_loaddata`.

#### Scenario: Fresh seed run populates blog tables
- **WHEN** `seed_loaddata` runs on a fresh database that already ran `base_loaddata`
- **THEN** the `Post`, `PostTranslation`, and `BlogImage` tables each contain at least one row

#### Scenario: Seed posts carry explicit slugs
- **WHEN** a seeded `Post` row is inspected
- **THEN** it has a non-empty explicit `slug` value supplied by the fixture, so `SlugBackfillMixin` leaves it untouched on load

#### Scenario: Base load excludes blog demo content
- **WHEN** only `base_loaddata` runs on a fresh database
- **THEN** no `Post`, `PostTranslation`, or `BlogImage` rows are created

#### Scenario: Idempotent on re-run
- **WHEN** `seed_loaddata` runs a second time against the same populated database
- **THEN** blog rows are matched by their explicit PKs and updated in place, and no blog table's row count increases

### Requirement: Seeded blog translations are bilingual
The system SHALL provide both an `es` and an `en` `PostTranslation` row for every seeded `Post`, satisfying `unique_together (post, language)` and the admin `TranslationInline` requirement of exactly two translations.

#### Scenario: Every seeded post has both languages
- **WHEN** a seeded `Post` row is inspected
- **THEN** it has exactly one `es` and one `en` translation row referencing it, each with `title`, `description`, `keywords`, and `content`

### Requirement: Blog seed media is readable from storage
The system SHALL commit sample media under `blog/fixtures/blog/seed/images/` at paths matching each model's `upload_to` (`blog/banners` for `Post.banner_image`, `blog/images` for `BlogImage.image`), and `seed_loaddata` SHALL write those files into the configured default storage so seeded image fields reference readable files.

#### Scenario: Banner images are readable
- **WHEN** a seeded `Post` row with a `banner_image` is loaded
- **THEN** the referenced file exists at `blog/banners/...` in the default storage (copied from the committed seed images)

#### Scenario: BlogImage files are readable
- **WHEN** a seeded `BlogImage` row is loaded
- **THEN** the referenced file exists at `blog/images/...` in the default storage (copied from the committed seed images), and files already present in storage are left untouched on re-run