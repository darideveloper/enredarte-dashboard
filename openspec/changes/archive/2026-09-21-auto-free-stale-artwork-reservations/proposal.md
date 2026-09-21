## Why

Closing the browser tab (or abandoning Stripe Checkout) leaves the artwork stuck in `RESERVED` ("Reservada") with a `PENDING_PAYMENT` order: `session_expires_at` is just a timestamp and nothing flips it back without a Stripe `checkout.session.expired` webhook, an externally-scheduled `release_expired_orders` cron, or a manual **Liberar reserva** action. This project has no Celery/Redis/worker (`docs/django-redis.md`), so a lost webhook means the next buyer gets `409 "Reserva en curso para esta obra."` indefinitely.

## What Changes

- Add a lazy, zero-infra reconciliation step: when `POST artworks/{slug}/buy/` or `GET artworks/{slug}/status/` encounters a `RESERVED` artwork with stale `PENDING_PAYMENT` order(s) (`session_expires_at` in the past), verify each stale order against Stripe newest-first (stop at the first paid-transition) before deciding.
- If Stripe reports `payment_status == "paid"`, apply the existing idempotent paid-transition (artwork → `SOLD`, order → `PAID_PENDING_DATA`, with the double-sale refund backstop) instead of freeing.
- If Stripe reports the session `status == "expired"` with `payment_status != "paid"`, apply the existing idempotent `cancel_order()` (order → `CANCELLED`, artwork → `AVAILABLE`). A session that is still `open` + unpaid (e.g. async OXXO/SPEI settling) keeps the hold even past local expiry.
- If Stripe is unreachable or the session state is unknown, fail closed: keep `RESERVED`, log, and return the current state (never `502` the status page, never cancel blind).
- Keep the 30-minute Stripe hold window unchanged; keep webhook, `release_expired_orders`, `sync_orders_from_stripe`, and admin **Liberar reserva** as-is (they become backstops, not the only path).

## Capabilities

### New Capabilities

(none — reconciliation reuses existing `artwork-sales` transitions; no new endpoint or model)

### Modified Capabilities

- `artwork-sales`: `POST buy/` reconciles stale hold(s) before returning `409` — a Stripe-expired hold is released and the request proceeds as a fresh `AVAILABLE` sale (`201`); a verified-paid hold becomes `SOLD` and returns `409 "Obra no disponible."`; an `open` + unpaid or unverifiable hold keeps the reservation (`409` as today).
- `artwork-status`: `GET status/` reconciles stale hold(s) before responding — a Stripe-expired hold is persisted as `AVAILABLE` and returned as such; a verified-paid hold is persisted as `SOLD`; an `open` + unpaid or unverifiable hold (Stripe error/unknown shape, `session_expires_at=None`) is returned stored (`reserved`) with no write.

## Impact

- Affected code: `artworks/services.py` (new reconcile helper), `artworks/views.py` (`buy` + `artwork_status`), `artworks/tests.py`, `docs/artwork-sales.md`, Bruno `Sales/POST buy.bru` + `Artworks/GET status.bru` docs blocks.
- No API shape changes (same request/response JSON, same status codes, same throttles `artwork_buys 20/hour` / `artwork_status 120/hour`).
- No new dependencies (reuses `subscriptions.services.stripe_client.retrieve_checkout_session`); no migration.
- Risk: `GET status/` performs a write on the stale path only (idempotent, row-locked); hot path (live hold / available / sold) makes zero Stripe calls.
