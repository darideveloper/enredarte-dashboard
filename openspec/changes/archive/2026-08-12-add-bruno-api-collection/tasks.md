## 1. Workspace scaffolding

- [x] 1.1 Create the `bruno/` workspace structure (workspace root + `bruno/collections/enredarte-dashboard-api/` with `environments/`, `Public Catalog/`, `Auth/`)
- [x] 1.2 Create `bruno/workspace.yml` with workspace metadata (`opencollection`, `info { name, type: workspace }`, `collections` pointing to `collections/enredarte-dashboard-api`)
- [x] 1.3 Create `bruno/collections/enredarte-dashboard-api/bruno.json` with collection metadata (`{"version": "1", "name": "Enredarte Dashboard API", "type": "collection"}`)

## 2. Environment

- [x] 2.1 Create `bruno/collections/enredarte-dashboard-api/environments/dev.bru` defining `base_url` (`https://enredarte-dashboard.localhost`) and `token` (placeholder), each with an `@description` comment

## 3. Requests

- [x] 3.1 Create the public catalog request `bruno/collections/enredarte-dashboard-api/Public Catalog/GET catalog.bru` targeting `GET {{base_url}}/api/catalog/` with `auth: none` and no headers
- [x] 3.2 Create the authenticated router-root request `bruno/collections/enredarte-dashboard-api/Auth/GET api root.bru` targeting `GET {{base_url}}/api/` with `headers { Authorization: Token {{token}} }`

## 4. Documentation

- [x] 4.1 Create `bruno/README.md` with steps to open the folder as a workspace in Bruno (select the folder containing `workspace.yml`), pick the `dev` environment (noting the portless subdomain prerequisite and the `http://localhost:8000` fallback), and the Django shell snippet to mint a DRF Token (`docs/django-drf.md` §6) to paste into `dev.bru`

## 5. Verification

- [x] 5.1 Verify both `.bru` request files reference only `{{base_url}}` / `{{token}}` (no hard-coded host or credential)
- [x] 5.2 Confirm `requirements.txt` and Python runtime files are unchanged
- [x] 5.3 Manual smoke test: with the dev server running (`./dev.sh`, portless subdomain `https://enredarte-dashboard.localhost`) and a valid token in `dev.bru`, the catalog request returns `200` without auth and the router-root request returns `200` with the token / `401` without it
- [x] 5.4 Confirm `bruno/workspace.yml` references an existing collection path and Bruno opens the folder without the `workspace.yml not found` error