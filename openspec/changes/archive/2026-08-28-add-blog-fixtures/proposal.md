## Why

The `blog` app has models (`Post`, `PostTranslation`, `BlogImage`) but no fixture data, so a fresh environment loads base + seed fixtures (via `seed_loaddata`) and the blog is the only business app left empty. Following the project's established fixture conventions, the blog should ship demo content so seeded environments and the admin have blog posts, translations, and media to work with — without any changes to the loader machinery.

## What Changes

- Add a `blog/fixtures/blog/seed/` fixture directory with three JSON files following the artworks seed pattern (explicit PKs, explicit timestamps, explicit slugs):
  - `00_Post.json` — two demo posts (Spanish-authored content), each with `banner_image`, `author`, `published_at`, `is_active`.
  - `01_PostTranslation.json` — both `es` and `en` translations per post (`title`, `description`, `keywords`, `content`), satisfying `unique_together (post, language)` and the admin's exact-2 translation inline.
  - `02_BlogImage.json` — two media-library rows (`name`, `image`).
- Add committed sample media under `blog/fixtures/blog/seed/images/` so `seed_loaddata`'s `_sync_seed_media` copies them into the default storage at the exact paths referenced by the fixtures:
  - `blog/banners/banner-1.jpg`, `blog/banners/banner-2.jpg` (used by `Post.banner_image`, upload_to `blog/banners`).
  - `blog/images/imagen-1.jpg`, `blog/images/imagen-2.jpg` (used by `BlogImage.image`, upload_to `blog/images`).
- Add blog tests mirroring the artworks seed tests: seed populates blog tables, re-runs are idempotent, `base_loaddata` does not create blog demo rows, and each seeded post has exactly 2 translations.
- Extend the "no business table left empty" seed expectation to include blog tables.
- No changes to `base_loaddata`, `seed_loaddata`, settings, `FIXTURE_DIRS`, or migrations. No new dependencies.

## Capabilities

### New Capabilities
- `blog-fixtures`: Blog seed fixture set — demo posts with bilingual translations and banners, media-library rows with synced sample images, loaded by `seed_loaddata` and excluded from `base_loaddata`, idempotent on re-run.

### Modified Capabilities
- `seed-content-completeness`: Extends the "every business model table" seed-coverage requirement so blog tables (`Post`, `PostTranslation`, `BlogImage`) are also populated by `seed_loaddata`, matching the existing artworks seed coverage.

## Impact

- **New files**: `blog/fixtures/blog/seed/00_Post.json`, `01_PostTranslation.json`, `02_BlogImage.json`; sample images `blog/fixtures/blog/seed/images/blog/banners/banner-{1,2}.jpg` and `blog/fixtures/blog/seed/images/blog/images/imagen-{1,2}.jpg`.
- **Tests**: new fixture test case in `blog/tests.py`.
- **Specs**: new `blog-fixtures` spec; delta for `seed-content-completeness`.
- **Unaffected**: fixture loader commands, settings, admin, serializers, views, migrations, existing artworks fixtures.