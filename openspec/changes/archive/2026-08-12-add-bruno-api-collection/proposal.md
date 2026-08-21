## Why

The project exposes a DRF API (`GET /api/catalog/`, `/api/` router root, future viewsets) but has no tooling to exercise it manually. Developers currently hand-craft curl commands or guess payloads, and there is no versioned, reviewable artifact documenting the API contract. A git-native API collection lets the whole team test and share requests against the DRF API with no cloud lock-in, no new runtime dependency, and full diffability in code review.

Bruno is chosen because it is open-source and stores collections as plain-text `.bru` files in the repo — unlike Postman (cloud sync, proprietary format) — which fits this repo's convention of documenting every decision in git.

## What Changes

- Add a `bruno/` directory at the repo root holding a version-controlled Bruno **workspace** (Bruno 3.0+ format): `bruno/workspace.yml` is the workspace root config.
- Add the collection under `bruno/collections/enredarte-dashboard-api/` with `bruno.json` declaring the collection (name, type, version).
- Add `bruno/collections/enredarte-dashboard-api/environments/dev.bru` defining `base_url` (the local dev server via the portless subdomain `https://enredarte-dashboard.localhost`, per `dev.sh`) and `token` (DRF Token placeholder).
- Add two initial request files:
  - `GET {{base_url}}/api/catalog/` — public catalog snapshot, no auth (`auth: none`).
  - `GET {{base_url}}/api/` — DRF router root, authenticated with `Authorization: Token {{token}}`.
- Requests reference only environment variables (`{{base_url}}`, `{{token}}`) so new environments (dev/prod) need a single file change.
- Add `bruno/README.md` with how to open the workspace in Bruno and how to obtain a DRF token (Django shell per `docs/django-drf.md` §6).
- No new Python dependencies; `requirements.txt` and runtime code are untouched.
- **BREAKING**: none.

## Capabilities

### New Capabilities

- `bruno-api-collection`: A git-native Bruno workspace (`bruno/` folder with `workspace.yml`) containing a `.bru` collection (`collections/enredarte-dashboard-api/`) with an environment file, a public catalog request, an authenticated router-root request, and a README, so the DRF API can be exercised manually and version-controlled.

### Modified Capabilities

## Impact

- **Code**: none — no Python files change; only the new `bruno/` directory.
- **APIs**: consumes `GET /api/catalog/` (public) and `GET /api/` (token-authenticated); documents both, does not modify them.
- **Dependencies**: none added; Bruno desktop app / `bru` CLI are developer tools only, not project dependencies.
- **Docs**: adds `bruno/README.md`; complements `docs/django-drf.md` (which documents how to create Tokens).
