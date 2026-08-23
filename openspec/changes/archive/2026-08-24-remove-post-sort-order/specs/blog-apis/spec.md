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
