## 1. Seed fixtures

- [x] 1.1 Create `blog/fixtures/blog/seed/00_Post.json` with 2 demo posts (explicit PKs, explicit `slug`, `author`, `published_at`, `banner_image` referencing `blog/banners/banner-{1,2}.jpg`, `is_active=true`, explicit `created_at`/`updated_at`), following the `artworks/fixtures/artworks/seed/*.json` format.
- [x] 1.2 Create `blog/fixtures/blog/seed/01_PostTranslation.json` with es + en rows for each post (fields `post`, `language`, `title`, `description`, `keywords`, `content`), satisfying `unique_together (post, language)`.
- [x] 1.3 Create `blog/fixtures/blog/seed/02_BlogImage.json` with 2 media-library rows (`name`, `image` referencing `blog/images/imagen-{1,2}.jpg`, explicit timestamps).
- [x] 1.4 Create sample media under `blog/fixtures/blog/seed/images/blog/banners/banner-1.jpg`, `banner-2.jpg` and `blog/images/imagen-1.jpg`, `imagen-2.jpg` (small valid JPGs) whose paths relative to `seed/images/` match the fixture field values and each model's `upload_to`.

## 2. Tests

- [x] 2.1 Add a blog fixture test case in `blog/tests.py` mirroring `artworks/tests.py` `SeedContentCompletenessTestCase`: after `call_command("seed_loaddata")`, `Post`, `PostTranslation`, and `BlogImage` counts are > 0.
- [x] 2.2 Add a test that each seeded post has exactly one `es` and one `en` translation.
- [x] 2.3 Add a test that `base_loaddata` alone creates no blog rows.
- [x] 2.4 Add a test that running `seed_loaddata` twice leaves blog row counts unchanged (idempotent).

## 3. Verification

- [x] 3.1 Run `python manage.py test blog` (and the full suite `python manage.py test`) — all pass, no artworks regressions.
- [x] 3.2 Manual dev check: `migrate` → `base_loaddata` → `seed_loaddata` (run twice), confirm 2 posts / 4 translations / 2 images, media present under `MEDIA_ROOT/blog/`, and blog list API returns the 2 posts newest-first.