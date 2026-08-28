## Context

The project loads fixed data through two thin commands in `core/management/commands/`:

- `base_loaddata` — scans every app's `<app>/fixtures/<app>/` for reference/lookup rows, run at every container start and in tests.
- `seed_loaddata` — scans `<app>/fixtures/<app>/seed/` for one-time demo content, run manually per environment; before loading it syncs committed files under `seed/images/` into the configured default storage via `default_storage` (`_sync_seed_media`), preserving paths relative to `seed/images/`.

Fixtures are hand-authored JSON per model: explicit PKs, explicit timestamps (honored over `auto_now`/`auto_now_add`), FKs as PKs, M2M as PK lists. Files load in alphabetical order, so numeric prefixes (`00_`, `01_`, …) enforce dependency order. The loader is fail-soft: each fixture is wrapped in a `try/except` and re-runs update rows in place by PK (idempotent).

The `artworks` app is the reference implementation (`artworks/fixtures/artworks/` base taxonomies + `seed/` demo content with `seed/images/artworks/obra-*.jpg`). The `blog` app (`Post`, `PostTranslation`, `BlogImage`) currently has **no** fixtures, so it is the only business app left empty by `seed_loaddata`.

The `blog` models:
- `Post(BaseModel)` → `banner_image` (upload_to `blog/banners`, null/blank), `author`, `published_at`, `slug`, `is_active`, `created_at`, `updated_at`.
- `PostTranslation(SlugBackfillMixin, TranslationBase)` → FK `post`, `title`, `description`, `keywords`, `content`, `language`; `unique_together (post, language)`; `slug_source = "title"`.
- `BlogImage(TimeStampedModel)` → `name`, `image` (upload_to `blog/images`, required).

The admin `PostTranslationInline` inherits `TranslationInline` from `artworks.admin`, which **requires exactly `len(settings.LANGUAGES)` = 2 translation rows** (es + en) and `can_delete = False`.

## Goals / Non-Goals

**Goals:**
- Ship a `blog/fixtures/blog/seed/` set that mirrors the artworks seed pattern, loaded automatically by the existing `seed_loaddata` with **zero changes** to loader code or settings.
- Every blog business table populated after a fresh `base_loaddata` + `seed_loaddata`.
- Sample media readable from storage at the exact paths the fixtures reference.
- Bilingual (es + en) translations per post so the admin inline invariant holds.
- Tests in `blog/tests.py` proving seed behavior and idempotency.

**Non-Goals:**
- No base (always-loaded) fixtures for blog — the app has no reference/lookup models; `base_loaddata` remains a no-op for blog.
- No changes to `base_loaddata`, `seed_loaddata`, `settings.py`, `FIXTURE_DIRS`, admin, serializers, views, or migrations.
- No new Python dependencies; no schema changes.

## Decisions

### 1. Seed-only tier, no base fixtures
Blog's models are authored content (posts) and media, not lookup/reference data. The docs' tier definition (`docs/django-fixtures.md`) maps them to seed. **Alternative rejected**: adding a base tier — it would conflate tiers and imply the app "needs" the data to function, which it does not.

### 2. Three fixture files with numeric prefixes
`00_Post.json` → `01_PostTranslation.json` (FK depends on `00_Post` PKs) → `02_BlogImage.json` (independent). Alphabetical sort of the `seed_loaddata` scan loads them in exactly this order. No cross-app dependencies exist (blog fixtures reference only blog PKs), so iteration order across apps is irrelevant.

### 3. Explicit slugs, PKs, and timestamps on every row
- Explicit `slug` per post → `SlugBackfillMixin.save()` is a no-op (`parent.slug` already set), matching the `slug-auto-generation` spec ("seed fixtures load rows that include explicit slug values").
- Explicit `published_at` per post with distinct dates → the public list API's newest-first ordering is deterministic.
- Explicit `created_at`/`updated_at` → deterministic rows despite `auto_now*`.

### 4. Media path mapping via `upload_to` parity
`_sync_seed_media` copies files preserving their path relative to `seed/images/`, and `loaddata` stores whatever path the field value contains. Therefore committed files must sit at:
- `blog/fixtures/blog/seed/images/blog/banners/banner-{1,2}.jpg` → stored at `blog/banners/banner-{1,2}.jpg` (matches `Post.banner_image` upload_to).
- `blog/fixtures/blog/seed/images/blog/images/imagen-{1,2}.jpg` → stored at `blog/images/imagen-{1,2}.jpg` (matches `BlogImage.image` upload_to).

The fixture field values reference exactly those storage paths. `_sync_seed_media` skips files already present, so re-runs never re-upload. **Alternative rejected**: reusing `artworks/obra-*.jpg` as blog banners — it couples blog fixtures to artworks seed having run and is semantically wrong.

### 5. Two demo posts, each with es + en
Two posts is enough to demo newest-first ordering and matches the existing blog test data shape. Both active and published. Each post gets exactly one `es` and one `en` `PostTranslation` row (satisfies `unique_together` and the admin exact-2 inline). **Alternative considered**: adding an inactive draft post — rejected as YAGNI; draft filtering is already covered by API tests.

### 6. Two `BlogImage` rows
Populates the media library (the project's seed convention is "no business table left empty", enforced by the `seed-content-completeness` spec) and makes the admin's copy-link action demoable. **Alternative rejected**: skipping `BlogImage` — it would leave the table empty and contradict the completeness convention.

### 7. App-local tests, no cross-app test edits
Blog fixture tests live in `blog/tests.py` (mirroring `artworks/tests.py` `SeedContentCompletenessTestCase`). The existing artworks completeness test asserts only artworks tables, so adding blog seed rows cannot break it; the new blog test asserts blog tables instead. This keeps app ownership of test coverage.

## Risks / Trade-offs

- **Binary sample images must be committed** → Generate four small placeholder JPGs (solid/gradient) at implementation time via a dev-time one-liner (PIL or ImageMagick — not a project dependency); verify they decode before committing.
- **Fixture content is hand-authored, not `dumpdata` output** → Follow the artworks fixture conventions exactly (explicit PKs/timestamps/slugs); JSON must contain no comments (JSON standard).
- **Seed posts will appear in the public API on seeded environments** → That is the intended behavior; `is_active` and `published_at` are set to plausible published values.
- **Admin exact-2 translation rule could reject a partially edited seeded post** → Seed provides both languages; the requirement mirrors the existing artworks workflow.
- **Path drift between `upload_to` and fixture field values** → Mitigated by the design decision to mirror `upload_to` under `seed/images/`; row loads are covered by the blog seed test (task 2.1), and synced-file presence is verified in the manual step (task 3.2) — matching the artworks convention, which performs no automated seed-media test.

## Migration Plan

1. Add the three JSON fixtures and four sample images.
2. Add the blog fixture test case.
3. Manual verification in a dev DB: `python manage.py migrate`, `python manage.py base_loaddata`, `python manage.py seed_loaddata` (twice — second run must not change counts), then check `/media/blog/banners/...` and `/media/blog/images/...` exist and the admin/API show the two posts.
4. Rollback: delete the fixture files and test case; no migrations or settings involved.

## Open Questions

None — scope and shape confirmed with the user (2 posts, banners yes, `BlogImage` yes, no OpenSpec-forcing of extra tiers).