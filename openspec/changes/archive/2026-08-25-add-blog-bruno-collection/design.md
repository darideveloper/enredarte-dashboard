## Context

See `proposal.md` for motivation. The Bruno collection in `bruno/collections/enredarte-dashboard-api/` contains 20 request files covering 10 models for `artworks` (sequences 1 to 20). The `blog` app exposes two public REST API endpoints (`GET /api/blog/posts/` and `GET /api/blog/posts/<slug>/`) which need dedicated `.bru` request files following the project's Bruno standards (`docs/django-bruno.md` and spec `bruno-request-docs`).

## Goals / Non-Goals

**Goals:**
- Create `bruno/collections/enredarte-dashboard-api/Posts/` folder.
- Create `GET list.bru` (`seq: 21`) and `GET detail.bru` (`seq: 22`).
- Include comprehensive `docs { ... }` blocks with exact response schemas, status codes (200, 404), and error envelopes matching `PostSummarySerializer`, `PostDetailSerializer`, and `project/handlers.py`.
- Update `bruno/README.md` to document the new `Posts` folder.

**Non-Goals:**
- Changes to backend DRF serializers, viewsets, or database models.

## Decisions

### 1. Folder Structure & Sequence Numbering
- **Decision**: Place requests under `bruno/collections/enredarte-dashboard-api/Posts/` with sequence numbers `seq: 21` (`GET list.bru`) and `seq: 22` (`GET detail.bru`).
- **Rationale**: Follows the existing pattern (`Artists/`, `Artworks/`, etc.) where sequence numbers incrementally order the collection tabs.

### 2. Public Authentication Configuration
- **Decision**: Configure `auth: none` and omit `headers { Authorization: ... }`.
- **Rationale**: `PostViewSet` uses `permission_classes = [AllowAny]`. Omitting unnecessary headers ensures users can test without generating a DRF auth token.

### 3. Comprehensive Docs Block
- **Decision**: Provide detailed Markdown in `docs { ... }` blocks with real JSON examples matching the pagination envelope (`count`, `page`, `results`) and error structure `{status: "error", message, data}`.
- **Rationale**: Fulfills the `bruno-request-docs` specification so developers can inspect response shapes directly inside Bruno.

## Risks / Trade-offs

- None (purely static API collection files; no runtime impact).
