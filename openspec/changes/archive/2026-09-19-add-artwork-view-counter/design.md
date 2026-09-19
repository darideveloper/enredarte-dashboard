## Context

`Artwork.views_count` (`artworks/models.py:384`, `PositiveIntegerField`, default `0`, "Visitas") backs `Artist.most_viewed` (`artworks/models.py:48-50`, `order_by("-views_count")`) and the admin "Más visitadas" block (`artworks/admin.py:690-695`). The field was specced as "a future public API/view will increment" (`artwork-discovery-flags`), but no such endpoint exists — values are admin-typed and fixtures sit at `0`.

`ArtworkViewSet` (`artworks/views.py:119`) is a `ReadOnlyModelViewSet` under the authenticated router (`artworks/urls.py:29`). Its only write action is public `POST buy` (`artworks/views.py:151-155`: `AllowAny`, empty `authentication_classes`, `ScopedRateThrottle` with scope set in `get_throttles()` at `:122-127`). Global default is `IsAuthenticated` + Token/Session auth (`project/settings.py:245-258`), with `artwork_buys`/`artwork_orders` throttle rates. User decisions for this change: public no-token access, raw increment (no dedup), return the new count.

## Goals / Non-Goals

**Goals:**
- Real frontend-driven counts: one `POST` per artwork detail view increments the counter atomically.
- Public access without tokens, capped by rate limiting.
- Frontend gets the fresh count back for live display.

**Non-Goals:**
- No per-visitor/per-IP/per-day dedup table or cache accounting.
- No changes to `most_viewed` ordering, admin form, serializers, or `buy`/order flows.
- No migration (field already exists).

## Decisions

**1. `POST artworks/{slug}/visit` detail `@action` on `ArtworkViewSet` — over hooking `retrieve()`, a standalone `APIView`, or `PATCH`.**
Reuses the router (no `urls.py` change), the slug-as-`pk` lookup convention from `buy`, and the active-only `get_queryset()` filter. The endpoint takes no input — any request body is ignored. `retrieve()`-hook rejected: list/detail `GET`s are cacheable and hit by prefetch/admin/bots, so increments would be unintentional and untestable in isolation. `PATCH` rejected: it implies arbitrary set and needs auth; this endpoint only ever `+1`.

**2. `AllowAny` + empty `authentication_classes` — over Token auth.**
The public site holds no machine token; matches the `buy`/`OrderSummaryView`/`OrderDeliveryView` precedent. Counter data is non-sensitive.

**3. `F("views_count") + 1` single-statement `update()` + `refresh_from_db` — over `select_for_update` or read-modify-write.**
Single-column counters are race-safe with `F()` at the DB level; `select_for_update` (used by `buy` for multi-step reservation) would serialize unnecessarily. No transaction wrapper needed.

**4. New `artwork_views` `ScopedRateThrottle` scope (`20/hour`) — over no throttle or strict dedup.**
Raw increment per user choice; the throttle is the only anti-bot lever this iteration, set to `20/hour` like `artwork_buys` per user decision (tighter than the `60/hour` first draft). Note the scope budget is per-client across all artworks (one shared quota per IP), not per-artwork — heavy multi-artwork browsing from one IP shares the budget. A dedicated scope (set via `get_throttles()` branch like `buy`) keeps catalog auth behavior untouched.

**5. `200 {"views_count": N}` — over `204`.**
Frontend displays the live number without a follow-up `GET` (which would stay `401` for anonymous callers anyway).

**6. Bruno request lives in `Artworks/` as `POST visit.bru` (`seq: 26`) — over `Sales/`.**
Visit is engagement tracking on the artwork resource, not part of the purchase flow. Uses a real active seed slug (`ciudad-reflejada`, so Send returns `200` on a seeded DB), `body: none`, no `headers` block, and a `docs` block per the `bruno-request-docs` convention. Guide notes in `bruno/README.md` and `docs/django-bruno.md` updated; the local `environments/dev.bru` is gitignored and out of scope for the change.

## Risks / Trade-offs

- [Refresh/bot inflation] → Mitigation: `20/hour` per-IP throttle + frontend guidance (once per detail mount, no retry, guard StrictMode double-effect). Accept residual inflation; revisit with IP/day dedup only if "Más visitados" measurably skews.
- [Slug enumeration probing increments random works] → Mitigation: `404` without side effects for unknown/inactive slugs; throttle bounds probing rate. Counts are low-stakes.
- [`get_throttles()` must branch on `action == "visit"`] → `ScopedRateThrottle` reads scope from the view, not the `@action` kwargs (existing `buy` gotcha, noted at `views.py:122-127`); missing the branch silently disables throttling. Covered by an explicit test.
