## 1. Runtime mount

- [x] 1.1 Change `project/urls.py:14` from `path("apis/artworks/", ...)` to `path("api/artworks/", ...)` (single-line fix; `artworks/urls.py` untouched)
- [x] 1.2 Update `artworks/tests.py` hardcoded paths: replace all `/apis/artworks/` with `/api/artworks/` (~19 strings at lines 1759–1954)

## 2. Bruno collection

- [x] 2.1 Update all 20 `.bru` files under `bruno/collections/enredarte-dashboard-api/*/{GET list.bru,GET detail.bru}`: `{{base_url}}/apis/artworks/` → `{{base_url}}/api/artworks/` (URL lines and `docs` comment lines)
- [x] 2.2 Update `bruno/README.md`: endpoint table (lines 54–71) and router-root mention from `/apis/artworks/` to `/api/artworks/`

## 3. Active specs

- [x] 3.1 Update `openspec/specs/artworks-rest-api/spec.md`: Purpose line plus every `/apis/artworks/` occurrence → `/api/artworks/` (auth + 6 resource requirements, routing requirement title + mount path, pagination `page_size` scenario, 404 scenario)
- [x] 3.2 Update `openspec/specs/artworks-api-bruno/spec.md`: list/detail URL patterns and README requirement → `/api/artworks/`
- [x] 3.3 Update `openspec/specs/bruno-api-collection/spec.md`: Purpose line, env-variables URL pattern, README requirement → `/api/artworks/`
- [x] 3.4 Update `openspec/specs/artist-subscription/spec.md`: 3 references to `GET /apis/artworks/artists/` → `GET /api/artworks/artists/`

## 4. Verify

- [x] 4.1 Run `rg "apis/"` (excluding `openspec/changes/archive/`) and confirm zero remaining hits
- [x] 4.2 Run `venv/bin/python manage.py test artworks blog --verbosity=2` and confirm green
- [x] 4.3 Smoke-test live: authenticated `GET /api/artworks/` lists 10 viewsets (200); `GET /apis/artworks/artists/` returns 404
- [x] 4.4 Confirm no `reverse()` or settings reference the old prefix (spot-check `project/settings.py`, `core/`, `subscriptions/`)

## 5. Coordinate + follow-up

- [x] 5.1 Notify the Astro landing repo owner to switch its build config to `/api/artworks/*` and rebuild after backend deploy
- [x] 5.2 Rebase in-progress change `add-artwork-stripe-sales` (old prefix in `proposal.md`, `design.md`, `specs/artwork-sales/spec.md`, `specs/artworks-rest-api/spec.md`)
- [x] 5.3 Rebase in-progress change `-artwork-mockups` (old prefix in `design.md`, `specs/artworks-rest-api/spec.md`)
