# blog-apis Specification

## Purpose
TBD - created by archiving change blog-apis. Update Purpose after archive.

## Requirements

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

### Requirement: Public Post Detail Endpoint by Slug
The system SHALL expose a public REST API endpoint `GET /api/blog/posts/{slug}/` that returns the full detailed blog post matching the slug with bilingual markdown content.

#### Scenario: Requesting single post detail by slug
- **WHEN** a client sends a `GET` request to `/api/blog/posts/{slug}/` with an active post's slug
- **THEN** the system SHALL return HTTP 200 with all summary fields plus `content_es` and `content_en`
- **AND** `content_es` and `content_en` SHALL contain the full markdown text for Spanish and English

#### Scenario: Requesting inactive or non-existent post
- **WHEN** a client sends a `GET` request to `/api/blog/posts/{slug}/` for a post that does not exist or has `is_active=False`
- **THEN** the system SHALL return HTTP 404 Not Found

### Requirement: Bruno Request Collection for Blog API
The system SHALL provide Bruno request files for the blog API in `bruno/collections/enredarte-dashboard-api/Posts/` covering both `GET list.bru` and `GET detail.bru` with complete `docs` blocks describing status codes, response shapes, and error structures.

#### Scenario: Blog posts list request in Bruno
- **WHEN** `bruno/collections/enredarte-dashboard-api/Posts/GET list.bru` is opened in Bruno
- **THEN** it targets `{{base_url}}/api/blog/posts/` with `auth: none` and contains a `docs` block documenting the paginated summary response and status 200.

#### Scenario: Blog post detail request in Bruno
- **WHEN** `bruno/collections/enredarte-dashboard-api/Posts/GET detail.bru` is opened in Bruno
- **THEN** it targets `{{base_url}}/api/blog/posts/:slug/` with `auth: none` and contains a `docs` block documenting the full detail response, status 200, and status 404 error envelope.
