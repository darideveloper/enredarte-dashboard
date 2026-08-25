## Why

The Django REST API endpoints for `artworks` are completely covered with 20 Bruno `.bru` request files, but the public REST API endpoints for `blog` (`/api/blog/posts/` and `/api/blog/posts/:slug/`) are missing from `bruno/collections/enredarte-dashboard-api/`. Adding Bruno request files with comprehensive `docs` blocks enables developers to explore and test the Blog API with pre-configured requests and live response examples.

## What Changes

- Create `bruno/collections/enredarte-dashboard-api/Posts/` directory.
- Create `bruno/collections/enredarte-dashboard-api/Posts/GET list.bru` (`seq: 21`) for public paginated post listings with complete response documentation.
- Create `bruno/collections/enredarte-dashboard-api/Posts/GET detail.bru` (`seq: 22`) for public post detail retrieval by slug with markdown content and error documentation.
- Update `bruno-api-collection` and `blog-apis` specifications.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `bruno-api-collection`: Extends the API collection structure to include the `Posts` endpoint group with public endpoints.
- `blog-apis`: Adds requirement for Bruno API collection coverage and documentation for blog posts endpoints.

## Impact

- **Files added**:
  - `bruno/collections/enredarte-dashboard-api/Posts/GET list.bru`
  - `bruno/collections/enredarte-dashboard-api/Posts/GET detail.bru`
- **Specs modified**:
  - `openspec/specs/bruno-api-collection/spec.md`
  - `openspec/specs/blog-apis/spec.md`
- **APIs/Backend**: Zero runtime backend code changes.
