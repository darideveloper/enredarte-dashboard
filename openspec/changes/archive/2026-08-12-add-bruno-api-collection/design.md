# Design: Add Bruno API collection

## Context

The project is a Django + DRF dashboard (Enredarte) serving a public catalog snapshot at `GET /api/catalog/` (`AllowAny`, `artworks/views.py`) and an (empty so far) DRF router root at `/api/` (`project/urls.py`). Global DRF settings (`project/settings.py:205`) use Token + Session authentication with a custom exception envelope and pagination. There is **no login endpoint**: API tokens are created manually in the Django shell/admin (`docs/django-drf.md` §6). The dev server runs via `dev.sh` under the `portless` proxy: the stable, documented access URL is the `https://enredarte-dashboard.localhost` subdomain (derived from the project dir name by `dev.sh`, per `docs/django-local-subdomain-setup.md`; both `enredarte.localhost` and `enredarte-dashboard.localhost` are in `ALLOWED_HOSTS` but only the latter is ever mapped by `portless`), while `http://localhost:8000` is only a fallback when port 8000 is free — `dev.sh` auto-increments to the next free port on conflict. The team has no tooling today to exercise the API manually, and the previous investigation confirmed Bruno as the chosen git-native API client (open-source, `.bru` plain-text collections, no cloud sync).

## Goals / Non-Goals

**Goals:**
- Version-controlled, reviewable Bruno collection for the DRF API.
- Requests parameterized via environment variables (`base_url`, `token`); zero hard-coded hosts/credentials.
- Cover the two existing endpoints: public catalog + token-authenticated router root.
- Self-contained usage docs (open in Bruno + how to mint a DRF Token).
- Zero changes to Python code, `requirements.txt`, or dependencies.

**Non-Goals:**
- Adding any endpoint (no login/token endpoint, no health check) — Bruno only consumes what exists.
- Automating token creation via a Bruno script (no login endpoint to drive it).
- CI integration / `bru run` smoke tests — deferred; only mentioned as a possible follow-up.
- Creating the Postman-style collection-level auth inheritance; auth is set per-request explicitly.

## Decisions

### 1. Store a Bruno workspace at repo root in `bruno/`
Bruno 3.0+ organizes work in **workspaces**: a folder with `workspace.yml` at its root and collections under `collections/`. This matches how other dev-tooling dirs live here and keeps the collection agnostic to Django app layout. The collection itself lives at `bruno/collections/enredarte-dashboard-api/`.
- **Alternative considered:** a standalone `.bru` collection folder at the root (no `workspace.yml`) — rejected after testing: the Bruno desktop **Open workspace** flow rejects such a folder with `Invalid workspace: workspace.yml not found`.
- **Alternative considered:** storing under `docs/` — rejected, it is not documentation prose; it is executable request definitions.
- **Alternative considered:** `tools/bruno/` — rejected, single-purpose dir `bruno/` is simpler and matches Bruno's own recommended layout.

### 2. Request files use `meta` + HTTP method blocks, env vars for everything dynamic
Following the current Bruno `.bru` format (verified against docs):
- Workspace metadata: `bruno/workspace.yml` with `opencollection: 1.0.0`, `info { name, type: workspace }`, and a `collections` list pointing at `collections/enredarte-dashboard-api`.
- Collection metadata: `bruno/collections/enredarte-dashboard-api/bruno.json` with `{ version: "1", name, type: collection }` (`collection.bru` is optional and only carries collection-level settings, none of which this collection needs).
- Environment: `bruno/collections/enredarte-dashboard-api/environments/dev.bru` with `vars { base_url, token }` and `@description` comments; `base_url` defaults to the portless subdomain `https://enredarte-dashboard.localhost` (`http://localhost:8000` only as a fallback when port 8000 is free).
- Catalog request: `get { url: {{base_url}}/api/catalog/, body: none, auth: none }`.
- Router-root request: `get { url: {{base_url}}/api/, body: none, auth: none }` plus a `headers { Authorization: Token {{token}} }` block.
- **Rationale:** env-driven URLs mean adding `dev.bru`/`prod.bru` later is a one-file copy. Explicit per-request `Authorization` header is the smallest correct mechanism for DRF's `Token <key>` scheme.

### 3. Auth is an explicit header, not Bruno collection-level auth inheritance
DRF uses `Authorization: Token <key>`. Setting `auth: inherit` would require collection-level bearer config that adds indirection for a single authenticated request. An explicit `headers` block is grep-able, diff-friendly, and requires no collection-level auth state.
- **Alternative considered:** Bruno `auth` block with bearer token var — rejected; DRF's scheme is `Token` (a bare word), which the bearer auth preset does not emit verbatim.

### 4. No dynamic token script
Bruno request scripts (`script: js`) can mint tokens at runtime, but this project has no login endpoint to hit. The `token` var is a placeholder the developer fills from the Django shell (`docs/django-drf.md` §6: `Token.objects.get_or_create(user=...)`).
- **Alternative considered:** pre-request JS to POST credentials to a nonexistent login URL — rejected; it would fail today and assume a login endpoint that is out of scope. Revisit when one exists.

### 5. README documents the two-step usage flow
`bruno/README.md` covers: open `bruno/` folder as a workspace in Bruno desktop (**Workspace dropdown → Open workspace**, selecting the folder with `workspace.yml`); pick `dev` environment; get a token; paste it; run the two requests.

## Risks / Trade-offs

- [`.bru` format drift across Bruno versions] → pinned to the documented format at implementation time; verified against `docs.usebruno.com`; a version bump is a small diff since files are plain text.
- [`token` placeholder could be committed/leaked] → `dev.bru` ships with a placeholder value; a real token is never stored (developer edits locally). If a real token were pasted, `dev.bru` is a plain diff-able file, so accidental commits are visible in review. `.gitignore` intentionally does NOT ignore it so the file template stays shared.
- [Only two requests now; future viewsets not covered] → collection folder structure (`<area>/` folders under `bruno/collections/enredarte-dashboard-api/`) is the extension point; adding a `.bru` file per new endpoint is the documented follow-up.
- [Base URL depends on the portless proxy being up] → the collection targets `https://enredarte-dashboard.localhost`, which requires `dev.sh` (portless) running; README states this prerequisite so a missing proxy is not mistaken for a Bruno misconfiguration.
- [No automated verification of the collection] → manual verification steps are listed in tasks; `bru run` CI smoke tests are a named follow-up, not part of this change.

## Migration Plan

Pure additive — no rollback needed. Create `bruno/`, commit. Existing tooling untouched.

## Open Questions

None — scope is fully determined by the two existing endpoints and the documented Token flow.
