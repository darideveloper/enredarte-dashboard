## Context

The landing (separate frontend codebase) bakes artwork `status` into static HTML via `getStaticPaths`. The dashboard backend owns the source of truth: `Artwork.status` (`available | sold | reserved | on_loan | not_available`, `artworks/models.py:257-262`), flipped `AVAILABLE → RESERVED` in `ArtworkViewSet.buy()` and `RESERVED → SOLD` in `services.apply_paid_transition()` (Stripe webhook), `RESERVED → AVAILABLE` on session expiry.

DRF defaults are auth-required (`IsAuthenticated`, `project/settings.py:255-256`), with exactly two public precedents on `ArtworkViewSet`: `POST .../buy/` and `POST .../visit/`, both `AllowAny + authentication_classes=[] + ScopedRateThrottle` (`artworks/views.py:153-157, 244-248`). Throttle scopes today: `artwork_buys 20/hour`, `artwork_orders 60/hour`, `artwork_views 20/hour` (`settings.py:264-268`). The Bruno collection documents each public endpoint with a `docs` block and no `Authorization` header (`bruno/collections/enredarte-dashboard-api/Artworks/POST visit.bru`).

## Goals / Non-Goals

**Goals:**
- Give the landing's BuyWidget island one cheap, auth-free, side-effect-free read to correct baked `status` within ~1s of mount.
- Follow the existing `visit()` public-action idiom exactly (permissions, 404 shape, throttle wiring) so review is mechanical.
- Document the endpoint in Bruno like every other public endpoint.

**Non-Goals:**
- No batch/multi-slug endpoint (catalog cards stay baked; accepted staleness for v1).
- No change to `buy/` codes (`409` stays; the `409`+`code` vs `404` debate is a separate change).
- No webhook/rebuild wiring, no SSR conversion, no hold-expiry logic changes.
- No exposure of order, buyer, or counter data.

## Decisions

### 1. `@action(detail=True, methods=["get"], url_path="status")` on `ArtworkViewSet`
Why: detail actions already resolve `<slug>` via the router (`artworks/urls.py:29`); the action receives the slug as `pk` and the existing `buy`/`visit` code looks it up with `slug=pk`. A separate `APIView` + manual route would duplicate router behavior for no benefit. Alternative (standalone `ArtworkStatusView`) rejected: more URL wiring, inconsistent with the two neighboring public actions.

### 2. Dedicated `artwork_status` throttle scope at `120/hour`, not reuse of `artwork_views`
Why: `20/hour` is tuned for counter increments; a detail mount fires status + visit together, and React StrictMode double-mounts plus one retry already burn 3 hits per view. A cheap single-row `SELECT` can afford `120/hour` while still capping scrapers. Alternative (reuse `artwork_views`) rejected: couples two unrelated budgets; a throttle on views would break status checks and vice versa. `get_throttles()` gains an `elif action == "status"` branch mirroring `views.py:122-129`.

### 3. Payload `{slug, status, status_display, price_mxn, price_usd, updated_at}` + `Cache-Control: no-store`
Why each field: `status` (enum switch), `status_display` (`get_status_display()`, backend owns Spanish copy), `price_*` (correct stale baked prices for free; DRF `DecimalField` serializes as string, matching `ArtworkSerializer`), `updated_at` (lets frontend/debug distinguish "API older than bake" from real flips). `no-store` closes the stale window; relaxing to `max-age=30` later is a header-only change if Cloudflare load demands it. Alternative (strict `{slug, status}`) rejected: saves ~60 bytes, loses price correction and debuggability. Alternative (full artwork detail, public) rejected: over-exposes images/translations and contradicts the catalog-stays-authenticated requirement.

### 4. Visibility filter `slug + is_active + artist__is_active`, 404 shape identical to `visit()`
Why: byte-identical `{status: error, message: Not found., data: {}}` means the frontend treats every non-200 as "keep baked HTML" with one code path. Query uses `.only(...)` single-row fetch — deliberately not the viewset's heavy prefetch `get_queryset()`. Alternative (reuse `get_queryset()` + `get_object()`) rejected: drags 8 prefetches for 6 fields.

### 5. Bruno file `Artworks/GET status.bru`, seq 27, public shape
Why: `visit` is seq 26, `buy` is seq 23, order-summary 24, order-delivery 25 — next free seq in the collection is 27 (avoids renumbering). Same two-part shape as siblings: `get { url: {{base_url}}/api/artworks/artworks/ciudad-reflejada/status/, auth: none }`, no `Authorization` header, `docs` block stating public + throttled + status codes + response JSON.

## Risks / Trade-offs

- [Risk] Catalog pages firing N single GETs if the frontend reuses this per card → throttle burn + herd. Mitigation: contract documents detail-mount usage only; batch endpoint is scoped as future work, explicitly not this change.
- [Risk] `RESERVED` can stick if the Stripe expiry webhook is ever missed (status stays reserved past the 30-min session). → Mitigation: out of scope here; surfaced as known limitation — frontend shows `Reservada` badge, and expiry handling stays with the webhook owner. No `reserved_until` field added (keeps contract minimal).
- [Risk] Scraper enumeration of slugs/prices. → Mitigation: slugs and prices are already public on the landing; `120/hour` per-client throttle bounds automated walks; no PII or order data exposed.
- [Risk] Cloudflare caching the GET despite `no-store` (misconfigured page rule). → Mitigation: verify response headers from the edge in the smoke task; `no-store` is origin-correct, edge config is ops-owned.
