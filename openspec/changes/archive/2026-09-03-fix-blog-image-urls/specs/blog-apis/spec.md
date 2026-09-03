## MODIFIED Requirements

### Requirement: Public Post Summary List Endpoint
The system SHALL expose a public REST API endpoint `GET /api/blog/posts/` that returns a paginated list of summarized active blog posts without full markdown content or sort order.

#### Scenario: Requesting blog post summaries
- **WHEN** an unauthenticated client sends a `GET` request to `/api/blog/posts/`
- **THEN** the system SHALL return HTTP 200 with a paginated envelope containing `count`, `next`, `previous`, `page`, `page_size`, `total_pages`, and `results`
- **AND** each item in `results` SHALL include `id`, `slug`, `author`, `banner_image`, `published_at`, `title_es`, `title_en`, `description_es`, `description_en`, `keywords_es`, and `keywords_en`
- **AND** `sort_order`, `content_es`, and `content_en` SHALL NOT be present in summary results

#### Scenario: Filtering and ordering active posts
- **WHEN** multiple blog posts exist in the database with varying `is_active` and `published_at` values
- **THEN** only posts where `is_active=True` SHALL be returned
- **AND** posts SHALL be ordered by descending `published_at` and descending `id`

#### Scenario: banner_image is absolute URL via get_media_url
- **WHEN** a post has a `banner_image` file
- **THEN** `banner_image` SHALL be an absolute URL produced by `utils/media.py:get_media_url` — `HOST` + relative path when stored locally, pass-through when stored on S3 (`s3.amazonaws.com`) or DigitalOcean Spaces (`digitaloceanspaces`), and relative fallback when `HOST` is empty.

#### Scenario: banner_image null when no file
- **WHEN** a post has no `banner_image` file
- **THEN** `banner_image` SHALL be `null`.

### Requirement: Public Post Detail Endpoint by Slug
The system SHALL expose a public REST API endpoint `GET /api/blog/posts/{slug}/` that returns the full detailed blog post matching the slug with bilingual markdown content.

#### Scenario: Requesting single post detail by slug
- **WHEN** a client sends a `GET` request to `/api/blog/posts/{slug}/` with an active post's slug
- **THEN** the system SHALL return HTTP 200 with all summary fields plus `content_es` and `content_en`
- **AND** `content_es` and `content_en` SHALL contain the full markdown text for Spanish and English

#### Scenario: banner_image absolute in detail
- **WHEN** a post has a `banner_image` file and is fetched by slug
- **THEN** `banner_image` SHALL follow the same absolute-URL contract as the list endpoint (`get_media_url`).

#### Scenario: Requesting inactive or non-existent post
- **WHEN** a client sends a `GET` request to `/api/blog/posts/{slug}/` for a post that does not exist or has `is_active=False`
- **THEN** the system SHALL return HTTP 404 Not Found

## ADDED Requirements

### Requirement: Blog image URLs use get_media_url
All blog image fields returned by the API (`Post.banner_image` on both list and detail) SHALL be serialized as absolute URLs using `get_media_url()` from `utils/media.py`, consistent with `artworks-rest-api: Image URLs use get_media_url`. The project SHALL use `HOST` from `project/settings.py` for the local-prefix branch and load `.env.{ENV}` with `override=True`.

#### Scenario: HOST setting defined
- **WHEN** `project/settings.py` is loaded
- **THEN** it SHALL expose `HOST` from the `HOST` environment variable.

#### Scenario: Local media prefixed with HOST
- **WHEN** a banner image is stored locally
- **THEN** `banner_image` SHALL be prefixed with `settings.HOST` (e.g., `https://enredarte-dashboard.example.com/media/blog/banners/banner-1.jpg`).

#### Scenario: S3 URLs passed through unchanged
- **WHEN** a banner image URL contains `s3.amazonaws.com` or `digitaloceanspaces`
- **THEN** `banner_image` SHALL be returned as-is without prefixing `HOST`.

#### Scenario: Missing HOST falls back to relative URL
- **WHEN** `settings.HOST` is empty
- **THEN** `get_media_url` SHALL return the relative URL (e.g., `/media/blog/banners/banner-1.jpg`) without crashing.

#### Scenario: Bruno docs reflect absolute URL
- **WHEN** `bruno/collections/enredarte-dashboard-api/Posts/GET list.bru` and `GET detail.bru` are inspected
- **THEN** their `docs` blocks SHALL describe `banner_image` as an absolute URL and example values SHALL be absolute (`https://.../media/blog/banners/...` or `https://...cdn.../enredarte/media/...`).
