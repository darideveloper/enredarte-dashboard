## 1. Reconcile helper

- [x] 1.1 Add `reconcile_stale_reservations(artwork)` to `artworks/services.py` with a two-phase contract (phase 1 lock-free: read stale orders + `retrieve_checkout_session`; phase 2 inside `select_for_update`: re-verify `RESERVED`/`PENDING_PAYMENT` then mutate): fast-path no-op for non-`RESERVED` / no stale `PENDING_PAYMENT` / live or `None` `session_expires_at` with zero Stripe calls; slow path iterates each stale order newest-first (stop at first paid-transition) — `paid` → paid-transition path (with `artwork_reserved_by` refund backstop), Stripe `expired` + unpaid → `cancel_order()`, `open` + unpaid → keep, Stripe error/unknown shape → fail closed with `logger.warning` and no mutation; parse the session via `sget`/getattr-dict fallback (`StripeObject` or `dict`)
- [x] 1.2 Cover helper with unit tests: live hold untouched with zero Stripe calls, `None` expiry untouched, expired+unpaid freed, expired+paid sold, `open`+unpaid past local expiry keeps hold with no write, Stripe exception keeps hold, `StripeObject` and `dict` session shapes both handled

## 2. Buy-path wiring

- [x] 2.1 Call the helper in `ArtworkViewSet.buy()` (`artworks/views.py`) before the `409` branch with the two-phase contract (Stripe fetch outside the existing `transaction.atomic() + select_for_update()` hold on the artwork row, re-check + transition + re-read the artwork row inside; the existing new-session creation inside `atomic()` stays): released → proceed as fresh `AVAILABLE` sale computed from the refreshed row, paid → `409 "Obra no disponible."` sold path, `open`+unpaid/unverifiable → `409` as today
- [x] 2.2 Add buy tests (mock `retrieve_checkout_session`): stale+expired second buyer gets `201` with new order, stale+paid gets `409 "Obra no disponible."` with artwork `SOLD`, stale+`open`/unpaid keeps `409` with hold intact, Stripe-down stale keeps `409` with hold intact, same-buyer live reuse still `200`

## 3. Status-path wiring

- [x] 3.1 Call the helper in `ArtworkViewSet.artwork_status()` with the two-phase contract (Stripe fetch before `select_for_update`, re-check + persist + re-read inside; build the response exclusively from the post-transition row): preserve `AllowAny`, `artwork_status` throttle, `.only(...)` hot-path read, `no-store`, and response shape; stale path persists before responding
- [x] 3.2 Add status tests: stale+expired returns `200 available` and persists `CANCELLED`/`AVAILABLE` (second call is a no-op read), stale+paid returns `200 sold` and persists, stale+`open`/unpaid returns `200 reserved` with no write, Stripe-down returns `200 reserved` with no write, every stale-path response carries the post-transition `updated_at` (never the pre-reconcile instance's), throttle/`404` behavior unchanged

## 4. Docs and contract

- [x] 4.1 Update `docs/artwork-sales.md` (flow + `409` row + buy workflow) to document lazy reconcile-then-decide on `buy`/`status`
- [x] 4.2 Update Bruno `Sales/POST buy.bru` and `Artworks/GET status.bru` `docs` blocks for the stale-hold behavior (no URL or JSON changes)
- [x] 4.3 Run `venv/bin/python manage.py test artworks subscriptions --verbosity=2` green plus a manual Bruno smoke (`buy` → expire/abandon → next `buy`/`status` frees) — DONE: 376 tests OK; live-Stripe Bruno smoke deferred to operator (no `bru` binary / test keys in this environment; flow covered by mocked tests)
