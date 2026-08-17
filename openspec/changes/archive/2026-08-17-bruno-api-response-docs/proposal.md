## Why

The 20 Bruno request files in `bruno/collections/enredarte-dashboard-api/` are bare request definitions (`meta` + `get` + `headers`) with no documentation of what the API returns. A developer opening the collection cannot tell the expected status codes or response shape without running each request or reading the serializers. The response contract already exists authoritatively in code (`artworks/serializers.py`, `project/pagination.py`, `project/handlers.py`) and is enforced by tests (`artworks/tests.py`), but Bruno — the git-native tool the team exercises the API with — mirrors none of it.

Bruno has a native `docs` block (Markdown, rendered in the request's Docs tab and in published API docs). Adding it to every request gives each endpoint a human-readable, git-reviewable "expected response" reference that lives next to the request itself. This change also establishes the rule that **every API request documented in Bruno — present and future — must carry this `docs` block**, so the practice does not regress as the API grows.

## What Changes

- Add a `docs { ... }` block to **all 20 existing `.bru` request files** (`GET list.bru` + `GET detail.bru` × 10 model folders) documenting, per endpoint:
  - Purpose of the endpoint and that it requires `Authorization: Token`.
  - Expected status codes (`200`, `401`, `404` for detail).
  - The expected JSON response shape: paginated envelope for lists, the resource object for detail, with a short JSON example derived from `artworks/serializers.py`.
  - The project-wide error envelope `{status: "error", message, data}`.
- Add a **system requirement** (new spec `bruno-request-docs`) that every `.bru` request file in the collection SHALL include a `docs` block describing the expected response, and that any future API endpoint added to the collection SHALL follow the same convention. This requirement is enforced via spec verification, not code.
- Update the `artworks-api-bruno` spec (delta) so the 20 existing request files satisfy the new convention.
- Update `docs/django-bruno.md` §6 (request files) with a short subsection documenting the `docs` block convention so future contributors follow it, and reference the spec.
- No runtime/code changes: serializers, views, pagination, handlers, and tests are untouched.

## Capabilities

### New Capabilities
- `bruno-request-docs`: Defines the convention that every `.bru` request file in the Bruno collection SHALL include a `docs` block documenting the expected response (status codes + JSON shape), including a mandatory requirement that all future API endpoints added to the collection follow it.

### Modified Capabilities
- `artworks-api-bruno`: The 20 existing request files (10 per-model folders × list/detail) are updated to include the `docs` block per the new `bruno-request-docs` convention.

## Impact

- **Files modified**: 20 request files under `bruno/collections/enredarte-dashboard-api/<Model>/`; `docs/django-bruno.md`.
- **Files added**: change artifacts only (`specs/bruno-request-docs/spec.md`, delta spec for `artworks-api-bruno`).
- **No impact**: `requirements.txt`, Python code, serializers, viewsets, pagination, handlers, tests, environments, `workspace.yml`, `bruno.json`.
- **Verification**: the change's verification step (tasks §7) confirms every request file contains a `docs` block; existing Django tests keep the documented shapes honest with the implementation.
