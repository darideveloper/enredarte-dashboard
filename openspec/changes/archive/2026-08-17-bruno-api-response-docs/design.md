## Context

The Bruno collection under `bruno/collections/enredarte-dashboard-api/` contains 20 `.bru` request files (10 model folders × `GET list.bru` + `GET detail.bru`) for the read-only DRF API under `/apis/artworks/`. Each file currently contains only `meta`, `get`, and `headers` blocks — no documentation of what the endpoint returns.

The response contract already lives authoritatively in code: `artworks/serializers.py` (per-resource field shapes), `project/pagination.py` (list envelope), `project/handlers.py` (error envelope), and is locked by `artworks/tests.py` (shape assertions). Bruno itself supports a native `docs` block (raw Markdown stored inside the `.bru` file) that renders in the request's Docs tab and in generated API docs, confirmed against the Bruno DSL parser (`docs = "docs" st* "{" nl* textblock tagend`).

This change documents every request with a `docs` block and establishes the convention as mandatory for future endpoints.

## Goals / Non-Goals

**Goals:**
- Every `.bru` request file in the collection has a `docs` block with purpose, auth requirement, status codes, and an expected-response JSON example derived from the actual serializers.
- The shapes documented are accurate mirrors of the code contract (no invented fields).
- The convention is written into `docs/django-bruno.md` and captured as a spec (`bruno-request-docs`) with a verification task, so future endpoints must follow it.
- Keep each `docs` block concise: one abbreviated list item / one resource object, not a full page of data.

**Non-Goals:**
- No changes to Python code, serializers, views, pagination, handlers, or tests.
- No OpenCollection YAML migration; the collection stays in `.bru` format.
- No `example` (saved-response) blocks and no `tests`/assertion blocks — this change is documentation only.
- No new environments, no changes to `workspace.yml`, `bruno.json`, or environment files.

## Decisions

**D1: Use the native `docs` block, not comments or saved examples.**
The `docs` block is the only Bruno-native, git-diffable place for hand-written Markdown per request, and it renders in the Docs tab and published docs. Alternatives considered:
- `example { ... }` blocks (saved responses) — require a live server + GUI capture, are read-only snapshots with real data, and bloat diffs; rejected for this documentation-only change.
- `tests` assertions — machine-checkable but this is a human-facing doc change; the contract is already covered by `artworks/tests.py`.
- Plain `#` comments in the file — not rendered by Bruno, invisible to consumers.

**D2: Derive every JSON example from the serializers, not from memory.**
List-item and detail shapes per resource are taken directly from `artworks/serializers.py` (field lists, `RefSerializer {id, slug}`, translation dicts, absolute media URLs, number types for prices) and `project/pagination.py` for the envelope. This keeps docs truthful and avoids drift.

**D3: One consistent docs template across all 20 files.**
All blocks share the same Markdown structure: `# <METHOD> /<resource>/ — <purpose>`, an auth note, `## Status codes`, and `## Response (200)` (plus `## Error (401)` and `## Error (404)` for detail). Uniformity makes the collection scannable and the spec checkable.

**D4: Enforce the convention via spec + docs, not a code guard.**
A spec requirement (`bruno-request-docs`) plus a `docs/django-bruno.md` subsection make the convention mandatory and discoverable. A code-level validator is out of scope (no runtime deps in `bruno/`, per existing spec).

## Risks / Trade-offs

- **[Docs drift from implementation]** → Shapes are derived from `artworks/serializers.py` at write time, and the existing `artworks/tests.py` assertions already pin the same shapes; the verify step in this change re-checks docs presence.
- **[Hand-written JSON examples get stale as fields change]** → Mitigated by keeping examples abbreviated (one item) and by the new convention: when serializers change, the docs block is part of the endpoint's definition and updated alongside.
- **[20 files of repetitive Markdown]** → Accepted; the template is small and the repetition is the point of a consistent collection reference.
