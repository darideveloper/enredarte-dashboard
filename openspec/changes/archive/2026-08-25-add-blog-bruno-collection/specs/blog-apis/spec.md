## ADDED Requirements

### Requirement: Bruno Request Collection for Blog API
The system SHALL provide Bruno request files for the blog API in `bruno/collections/enredarte-dashboard-api/Posts/` covering both `GET list.bru` and `GET detail.bru` with complete `docs` blocks describing status codes, response shapes, and error structures.

#### Scenario: Blog posts list request in Bruno
- **WHEN** `bruno/collections/enredarte-dashboard-api/Posts/GET list.bru` is opened in Bruno
- **THEN** it targets `{{base_url}}/api/blog/posts/` with `auth: none` and contains a `docs` block documenting the paginated summary response and status 200.

#### Scenario: Blog post detail request in Bruno
- **WHEN** `bruno/collections/enredarte-dashboard-api/Posts/GET detail.bru` is opened in Bruno
- **THEN** it targets `{{base_url}}/api/blog/posts/:slug/` with `auth: none` and contains a `docs` block documenting the full detail response, status 200, and status 404 error envelope.
