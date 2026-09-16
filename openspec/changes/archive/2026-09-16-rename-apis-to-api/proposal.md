## Why

The artworks API is mounted at `/apis/artworks/` (plural) while the project's API convention is the singular `/api/` prefix (as in `/api/blog/`) and all project documentation already describes `/api/artworks/` as the canonical path. The mismatch confuses API consumers (notably the separate Astro landing repo that builds against these endpoints) and contradicts the documented standard. Align the code to the documented convention now, before more clients hard-code the typo'd prefix.

## What Changes

- **BREAKING**: Move the artworks router mount in `project/urls.py` from `apis/artworks/` to `api/artworks/`; all 21 endpoints (router root + 10 list + 10 detail) move together with no behavior change.
- **BREAKING**: Old `/apis/artworks/*` URLs stop working (404). No redirect shim and no dual-mount period — direct cutover per decision.
- Update all in-repo consumers of the old prefix: `artworks/tests.py` (~19 hardcoded path strings), 20 Bruno request files under `bruno/collections/enredarte-dashboard-api/*/`, and `bruno/README.md`.
- Update active OpenSpec specs that encode the `/apis/` prefix (`artworks-rest-api`, `artworks-api-bruno`, `bruno-api-collection`, `artist-subscription` references).
- Archived change docs under `openspec/changes/archive/` are history and stay untouched; `docs/` already describes `/api/` and needs no change.

## Capabilities

### New Capabilities

- None — no new behavior is introduced.

### Modified Capabilities

- `artworks-rest-api`: endpoint address requirement changes from `/apis/artworks/` to `/api/artworks/` (all 10 resources plus router root).
- `artworks-api-bruno`: Bruno `GET list.bru` / `GET detail.bru` URL requirement changes to `{{base_url}}/api/artworks/<resource>/`.
- `bruno-api-collection`: collection URL-pattern requirement changes to `{{base_url}}/api/artworks/<resource>/`.
- `artist-subscription`: incidental references to `GET /apis/artworks/artists/` updated to the new prefix (exclusion behavior unchanged).

## Impact

- Affected code: `project/urls.py` (1 line), `artworks/tests.py`, 20× `.bru` files, `bruno/README.md`, 4 active spec files.
- `artworks/urls.py` (router registrations) is untouched — the prefix lives only in the mount point.
- No Python code resolves these URLs via `reverse()` (all `reverse()` usage is `admin:*`, `blog-posts-*`, `subscriptions:*`), so no logic changes are needed.
- External impact: any client calling `/apis/artworks/*` (e.g., the Astro landing build) must switch to `/api/artworks/*`; coordination with the landing repo is the only out-of-repo work.
- In-progress changes overlap and will need a rebase after this lands: `add-artwork-stripe-sales` references the old prefix in `proposal.md`, `design.md`, `specs/artwork-sales/spec.md` (new buy/order/delivery endpoints), and `specs/artworks-rest-api/spec.md`; `-artwork-mockups` references it in `design.md` and `specs/artworks-rest-api/spec.md`.
