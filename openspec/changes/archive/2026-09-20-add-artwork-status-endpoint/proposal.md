## Why

The public landing bakes artwork `status` into static HTML at build time (`getStaticPaths`). Every sale leaves the page stale until a manual rebuild, so buyers see "Disponible" for already-sold works and hit a confusing `409 "Obra no disponible."` on `buy/` instead of a `Vendida` badge.

## What Changes

- Add one public, auth-free read endpoint: `GET /api/artworks/artworks/<slug>/status/` returning live `{slug, status, status_display, price_mxn, price_usd, updated_at}` with `Cache-Control: no-store`.
- Throttle it with a dedicated `artwork_status` `ScopedRateThrottle` scope at `120/hour` per client instead of reusing `artwork_views`.
- Return `404 {status: error, message: Not found., data: {}}` for unknown slugs, inactive artworks, and inactive artists (same shape as `visit/` / `buy/`).
- Keep the catalog list/detail endpoints authenticated; `status/` becomes a named public exception alongside `buy/` and `visit/`.
- Ship a Bruno request file `Artworks/GET status.bru` (public, no auth header, documented like `POST visit.bru`).
- No change to `buy/` status codes, no batch endpoint, no webhook/rebuild wiring, no SSR conversion (explicitly out of scope).

## Capabilities

### New Capabilities

- `artwork-status`: public single-artwork live status check (contract, visibility rules, throttling, caching, frontend swap semantics).

### Modified Capabilities

- `artworks-rest-api`: add `GET artworks/{slug}/status/` to the named list of public exceptions; catalog list/detail stay authenticated.
- `bruno-api-collection`: add `Artworks/GET status.bru` public request with `docs` block (no `Authorization` header, `{{base_url}}` only).

## Impact

- Backend: `artworks/views.py` (new `@action` on `ArtworkViewSet` + `get_throttles` branch), `project/settings.py` (new `artwork_status` throttle rate), `artworks/tests.py` (new test cases mirroring `VisitArtworkApiTestCase`).
- API surface: one new `GET` route under `/api/artworks/`; no breaking changes to existing routes, serializers, or auth.
- Docs/ops: one new `.bru` file; landing `BuyWidget` island fetches on mount (separate frontend codebase, non-normative here). No new infra, secrets, or dependencies.
