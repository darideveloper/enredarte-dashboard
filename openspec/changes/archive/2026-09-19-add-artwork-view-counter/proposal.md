## Why

`Artwork.views_count` (the "Visitas" counter behind the artist profile's "Más visitados" block) is still manual-only: admins type numbers into the change form and seed fixtures sit at `0`. The public frontend has no way to report real detail-page views, so the block never reflects actual traffic.

## What Changes

- Add a public `POST /api/artworks/artworks/{slug}/visit/` endpoint that atomically increments `views_count` by 1 and returns the new count as `{"views_count": N}`.
- No authentication required (same public pattern as `buy` / order endpoints); abuse is contained with a new `artwork_views` `ScopedRateThrottle` rate (`20/hour` per client, same as `artwork_buys`).
- Inactive or missing artworks return `404` and are never incremented.
- Bruno coverage: new `Artworks/POST visit.bru` request (seq 26) with a `docs` block per the `bruno-request-docs` convention, plus public-endpoint notes in `bruno/README.md` and `docs/django-bruno.md`.
- Everything else is unchanged: `views_count` stays admin-editable, `Artist.most_viewed` ordering is untouched, no dedup table or per-IP accounting in this iteration.

## Capabilities

### New Capabilities

- `artwork-view-tracking`: public increment endpoint for artwork detail views — request/response shape, atomic `+1`, `404` behavior, throttle scope, and frontend call contract (once per detail mount, fire-and-forget).

### Modified Capabilities

- `artworks-rest-api`: adds `POST artworks/{slug}/visit/` to the list of public exceptions alongside the artwork-sales endpoints; catalog list/detail stays authenticated.
- `artwork-discovery-flags`: activates the "future public API/view will increment" scenario — the counter is now incremented by a real endpoint instead of admin-only edits.

## Impact

- `artworks/views.py`: new `visit` detail `@action` on `ArtworkViewSet` + `get_throttles()` scope branch.
- `project/settings.py`: new `artwork_views` entry in `DEFAULT_THROTTLE_RATES`.
- `artworks/tests.py`: new tests for increment, `404`, unauthenticated access, raw re-increment, throttle wiring, and `429` enforcement.
- `bruno/collections/enredarte-dashboard-api/Artworks/POST visit.bru` (new) + public-endpoint notes in `bruno/README.md` and `docs/django-bruno.md`.
- Public frontend: one fire-and-forget `POST` per artwork detail mount; no auth header needed.
- No migrations, no serializer/admin changes, no new dependencies.
