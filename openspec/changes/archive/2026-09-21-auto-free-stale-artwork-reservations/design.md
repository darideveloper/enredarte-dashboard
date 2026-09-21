## Context

`POST artworks/{slug}/buy/` (`artworks/views.py:160-244`) flips `AVAILABLE → RESERVED` and creates an `ArtworkOrder(PENDING_PAYMENT)` with a 30-minute Stripe Checkout Session (`session_expires_at`). The hold is released today only by `checkout.session.expired` / `async_payment_failed` webhooks (`subscriptions/webhooks.py:94-122` → `artworks/services.py:41-52` `cancel_order()`), the external-cron `release_expired_orders` command, `sync_orders_from_stripe`, or manual admin **Liberar reserva**. There is no Celery/Redis/worker in this repo (`docs/django-redis.md`, `start.sh` runs only gunicorn), so a lost webhook plus no cron leaves the artwork stuck in `RESERVED` — the next buyer gets `409 "Reserva en curso para esta obra."` forever. The `GET artworks/{slug}/status/` endpoint (`views.py:263-289`) is currently read-only (`.only(...)` fetch, `Cache-Control: no-store`, `artwork_status 120/hour`).

## Goals / Non-Goals

**Goals:**
- Abandoned holds (tab close, Checkout abandon) self-heal on next traffic with zero new infrastructure.
- Never cancel a just-paid order: reconcile against Stripe before any release (paid → `SOLD`, expired/unpaid → `AVAILABLE`).
- Reuse existing transitions (`cancel_order`, `apply_paid_transition` + double-sale refund backstop) — no new lifecycle states, no migration, no new deps.

**Non-Goals:**
- Changing the 30-minute hold window, webhook handlers, cron commands, admin actions, API shapes, throttles, or catalog list behavior.
- Adding Celery/Redis/APScheduler/in-process timers or any background worker.

## Decisions

- **D1 — New `reconcile_stale_reservations(artwork)` helper in `artworks/services.py` (over blind TTL release).** Fast path with zero Stripe I/O: `status != RESERVED`, no stale `PENDING_PAYMENT` order (`session_expires_at` future or `None`) → return `(changed=False, reason)`. Slow path (at least one stale order): for each stale order newest-first, `stripe_client.retrieve_checkout_session()` (parsed via `sget`/getattr-dict fallback — the call returns a `StripeObject` or `dict` depending on path, same as the webhook/sync readers) then branch — `payment_status == "paid"` → paid-transition path (same semantics as `_apply_artwork_paid` including `artwork_reserved_by` refund backstop; stop looping, artwork is `SOLD`); session `status == "expired"` with `payment_status != "paid"` → `cancel_order()` and continue; session still `open` + unpaid → keep (no-op, reservation holds for async settlement); Stripe exception/unknown shape → fail closed (keep `RESERVED`, `logger.warning`, no raise). Alternative (local timestamp only) rejected: it would cancel paid-but-webhook-delayed orders and `open` async sessions.
- **D2 — Two-phase contract: Stripe outside the lock, mutate + re-read inside.** Phase 1 (no lock): read the artwork + stale orders, call Stripe. Phase 2 (`transaction.atomic() + select_for_update()`): re-check `artwork.status == RESERVED` and `order.status == PENDING_PAYMENT`, apply the decided transition, then re-read the artwork row (`refresh_from_db` / re-fetch) before building any response — responses SHALL be built exclusively from the post-transition row, never from the pre-reconcile instance (otherwise `status`/`status_display`/`updated_at` go out stale). Rationale: never hold a Postgres row lock across network I/O; concurrent visitors converge via the idempotency guards (second completer is a no-op). Note: the existing `buy` flow already creates its *new* Checkout Session inside its `atomic()` block — that stays as-is; only the reconcile read is split out. Alternative (everything inside one lock, or responding from the pre-reconcile instance) rejected: lock-hold amplification under slow Stripe, plus stale reads.
- **D3 — Accept a write on `GET status/` on the stale path only.** Hot path (available/sold/live-reserved) stays a single-row read. Stale path persists the reconciled state so the next reader/cron sees the truth (no read/DB divergence). Guarded by existing `artwork_status 120/hour` throttle + `no-store` + row lock + idempotent transitions. Alternative (report-only effective status) rejected per operator choice: it leaves DB stale and complicates `buy` re-entry.
- **D4 — Reconcile all stale `PENDING_PAYMENT` orders for the artwork, newest first.** Invariant is one pending per artwork, but defensive loop handles duplicates from retried buys; stops at first paid-transition (artwork now `SOLD`).
- **D5 — Fail closed everywhere.** `retrieve_checkout_session` raising, returning an unparseable shape, or a `None` expiry → keep `RESERVED`, `logger.warning`, return stored state (`buy` → `409` as today; `status` → `200 reserved`). The status endpoint SHALL never `502` due to Stripe.

## Risks / Trade-offs

- [Risk] Added Stripe latency on stale hits (one `retrieve` per stale order) → Mitigation: only on the stale path (rare, once per 30-min hold); bounded by the Stripe SDK default timeout (no new timeout plumbing in this change); result persisted so followers hit the fast path.
- [Risk] Two visitors reconcile concurrently (double Stripe read + double transition) → Mitigation: Phase-2 re-check plus transitions guarding on `status == PENDING_PAYMENT`; second completer is a no-op; refund backstop covers paid/paid races. Concurrent duplicate `retrieve` calls before the first persist are harmless (read-only).
- [Risk] OXXO/SPEI async settling near expiry → Mitigation: decision comes from live Stripe `payment_status`/`status`, not the local clock; `unpaid` + non-expired session keeps the hold (same rule as `sync_orders_from_stripe`).
- [Risk] `GET` performing writes surprises purists/caches → Mitigation: documented in spec + Bruno docs; `no-store` preserved; write is idempotent single-row state repair, not user data creation.

## Migration Plan

No migration. Deploy normally (Coolify via existing flow); no rollback steps beyond revert — worst case reverted code behaves exactly as today (webhook/cron/manual release). Optional follow-up (not in this change): schedule `release_expired_orders` every 10 min as a backstop for zero-traffic artworks.
