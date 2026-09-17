# Design: add-artwork-stripe-sales

## Context

The dashboard is a Django 5.2 + DRF admin for the Enredarte gallery; the
public site is a separate frontend consuming `/api/artworks/` (catalog API,
read-only, token-authenticated for builds). Stripe is already integrated for
artist subscriptions: `subscriptions/services/stripe_client.py` is the only
module importing `stripe` (project invariant), `POST /webhooks/stripe/` does
signature verification + `StripeEvent` unique-index idempotency + atomic
handlers (see `openspec/specs/stripe-webhook-handler/`), and admin actions
live on the Artist change page.

`Artwork` already carries `price_mxn` / `price_usd` (Decimal) and an
`ArtworkStatus` enum that includes `available`, `reserved`, `sold`. The new
sales flow rides on top of these instead of introducing parallel concepts.

Decisions locked with the operator during exploration:
- Buyer picks currency (MXN/USD) at buy time.
- Reserve on buy-click (not first-payment-wins).
- Track shipped/delivered in the dashboard.
- Redirect URLs via new `PUBLIC_SITE_URL` env var (frontend-hosted pages).

## Goals / Non-Goals

**Goals:**
- Visitor buys a unique artwork end-to-end: buy → Stripe Checkout → pay →
  delivery form → operator ships.
- Zero double-sales for unique inventory; graceful cancel/expire everywhere.
- Maximal reuse of the existing subscription Stripe plumbing.

**Non-Goals:**
- No cart / multi-item checkout (each artwork is a unique physical object).
- No Stripe Product/Price objects per artwork (inline `price_data`).
- No customer accounts, no saved addresses, no Stripe Customer Portal for
  buyers.
- No shipping-cost calculation or tax engine; charge = artwork price.
- No new webhook endpoint or secret (reuse `/webhooks/stripe/`).
- No changes to the public catalog API contract.

## Decisions

### D1. One `ArtworkOrder` model, delivery fields flat on it
- `ArtworkOrder` in the `artworks` app (not a new app; fewest files) with
  `BaseModel` (uuid-hex slug = unguessable order token), `artwork` FK
  `PROTECT`, status enum `pending_payment / paid_pending_data / data_complete
  / shipped / delivered / cancelled / refunded`, `currency` (`mxn|usd`),
  `amount` (Decimal snapshot), `stripe_checkout_session_id`, `checkout_url`,
  `session_expires_at`, `stripe_payment_intent_id`, `buyer_email` (captured
  from the buy request — the frontend collects it on the buy screen —
  normalized lowercase; the reservation owner), `buyer_name` (from Stripe),
  `paid_at`, `cancelled_at`, and flat delivery columns (`receiver_name`,
  `receiver_phone`, `country`, `state`, `city`, `postal_code`,
  `neighborhood`, `street`, `exterior_number`, optional `interior_number`,
  `between_street_1`, `between_street_2`, `reference`, `delivery_notes`).
- **Why flat delivery fields?** One row per sale; a separate `DeliveryInfo`
  model adds a join for zero benefit (YAGNI). If multi-shipment ever appears,
  extract then.
- **Why order-level "paid_pending_data" instead of an artwork status?** The
  artwork is a physical unique object: it is simply `reserved` → `sold`. The
  "paid but waiting delivery info" nuance belongs to the transaction, so the
  operator reads one orders list. `ArtworkStatus` stays untouched.
- **Why uuid slug as the public token?** `BaseModel.slug` already exists and
  is unique; no extra token field, no signing machinery. Slug is uuid-hex
  (generated like `ArtworkGallery.save()` does), not derived from content, so
  it is unguessable.

### D2. Checkout Session with inline `price_data`, subscription machinery untouched
- `create_artwork_checkout_session(amount, currency, customer_email, metadata,
  success_url, cancel_url, expires_at)` in `subscriptions/services/stripe_client.py`
  (all new Stripe API calls go through `stripe_client`; note the historical
  "only module imports stripe" invariant already has one pre-existing
  exception in `artworks/admin.py`, untouched by this change). Uses
  `stripe.checkout.Session.create(mode="payment",
  line_items=[{"price_data": {"currency": cur, "unit_amount":
  int(amount*100), "product_data": {"name": artwork_title}}, "quantity": 1}],
  customer_email=customer_email, expires_at=now+30min, metadata=...,
  success_url=..., cancel_url=...)`. `customer_email` prefills **and locks**
  the email in Checkout, so the paying email always matches the reservation
  owner stored on the order.
- **Why not sync artwork prices to Stripe Products/Prices?** One-off sessions
  accept inline price data; syncing would add product/price lifecycle admin,
  archiving on price edit, and migration surface for zero benefit. The
  subscription `BillingPlan` flow is orthogonal and stays as-is.
- Also added to stripe_client: `retrieve_checkout_session(session_id)` (paid
  verification backstop) and `create_refund(payment_intent_id)` (double-sale
  backstop).
- Stripe v15 note: `amount` conversions reuse the `Decimal`-safe patterns
  already established in `plan_sync.py` (`int(Decimal(amount) * 100)`).

### D3. Webhook routing on `metadata.kind`
- `checkout.session.completed` / `.expired` / `.async_payment_succeeded` /
  `.async_payment_failed` handlers first read `metadata.kind`:
  `"artwork_order"` → new artwork handlers (correlate `metadata.order` →
  `ArtworkOrder` slug); anything else → existing subscription behavior,
  byte-for-byte unchanged.
- Completed handler: only transitions on `payment_status == "paid"` (unpaid
  sessions stay `pending_payment`, reservation holds — final confirmation
  arrives via `async_payment_*`). If order is `pending_payment` → store
  payment intent + buyer identity + `paid_at`, set `paid_pending_data`,
  artwork → `sold`. If artwork no longer reservable (sold by someone else) →
  order `refunded` + `create_refund(payment_intent)` backstop (D5).
- `async_payment_succeeded` handler: same idempotent paid-transition as the
  completed handler, only from `pending_payment` (includes refund backstop).
- `async_payment_failed` handler: order still `pending_payment` →
  `cancelled` + `cancelled_at`, artwork → `available`.
- Expired handler: order still `pending_payment` → `cancelled`,
  artwork → `available`. Idempotent by design (second delivery is a no-op via
  `StripeEvent` + status guards).
- All inside the existing `transaction.atomic()` + `StripeEvent` insert —
  retry/idempotency semantics inherited for free.
- Subscription-mode sessions created before this change have no `metadata.kind`;
  absence of the key routes to legacy behavior — no migration needed.

### D4. Buy endpoint concurrency: `select_for_update` + status guard + same-buyer reuse
```
with transaction.atomic():
    artwork = Artwork.objects.select_for_update().get(slug=..., is_active=True)
    email = request.data["email"].strip().lower()   # serializer-validated
    if artwork.status == RESERVED:
        pending = artwork.orders.filter(status=PENDING_PAYMENT).first()
        if pending and pending.session_expires_at > now() \
           and pending.buyer_email == email:
            return 200 {"checkout_url": pending.checkout_url}  # same buyer reuse
        return 409  # someone else's live reservation (or dead session awaiting expiry webhook)
    if artwork.status != AVAILABLE: return 409
    artwork.status = RESERVED
    order = ArtworkOrder.objects.create(artwork=..., status=PENDING_PAYMENT,
                                        currency=..., amount=..., buyer_email=email,
                                        slug=uuid-hex)
    session = create_artwork_checkout_session(..., customer_email=email, ...)
    order.stripe_checkout_session_id = session.id
    order.checkout_url = session.url
    order.session_expires_at = session.expires_at (epoch→datetime)
    order.save()
```
- The DB row lock closes the two-buyers race; the `status != available`
  re-check inside the lock is the real guard.
- **Same-buyer reuse** (operator decision): the buy screen collects the email
  first, so a buyer who cancelled or refreshed can re-click buy and get the
  same live Checkout URL instead of a 30-minute `409` lockout. Reuse matches
  `buyer_email` case-insensitively and requires `session_expires_at` in the
  future; reuse forces the original currency for the session's remaining TTL
  (accepted trade-off — after expiry the buyer picks again). This mirrors the
  subscriptions `expire_or_reuse_session` convention already in
  `stripe_client.py`. A different email (or an expired session still awaiting
  the expiry webhook) gets `409`.
- **Known ceiling (`ponytail:`):** the Stripe call sits inside the
  transaction; a slow Stripe adds lock hold time on a single row — fine at
  gallery traffic (a handful of buys/day). If Stripe outage leaves rows
  `reserved` with a dead session, the admin **Liberar reserva** action is the
  manual escape hatch; `checkout.session.expired` is the automatic one. If a
  create fails mid-request, the whole tx rolls back (artwork back to
  `available`) — no orphan reservations from failed creates.
- Alternative rejected (first-payment-wins): simpler code but produces real
  double-charges on a physical unique good — refund UX is worse than a 409.
- Verification note (2026-09-17): true concurrent contention proven by
  `select_for_update` + sequential guard tests only; operator accepted
  without a staging race run.

### D5. Double-sale backstop: auto-refund
- Reservation is not perfect (webhook loss, operator error, clock edge cases).
  On `checkout.session.completed`, if the artwork is no longer sold-by-this-
  order, refund the payment intent via Stripe and mark the order `refunded`.
- Failure path: refund API error → `logger.exception` → handler raises →
  500 → Stripe retries the event (existing retry semantics) → refund retried
  next delivery. No partial state persists (atomic block).
- Money-loss ceiling documented: refund amount = full session amount; Stripe
  fees are not recovered. Acceptable at gallery volumes.

### D6. Public endpoints, no auth, scoped throttle
- Three public endpoints under the artworks router with
  `permission_classes=[AllowAny]` + scoped `AnonRateThrottle`
  (`buys`: e.g. `20/hour`, `orders`: `60/hour`) — tight on buy (money path),
  looser on read. DRF settings get a named throttle scope; catalog endpoints
  stay token-authenticated (`artworks-rest-api` delta).
- SessionAuthentication is not used by these views, so no CSRF concerns for
  the SPA.
- **Webhook-race fallback on the summary endpoint**: the Stripe success
  redirect can beat the `checkout.session.completed` webhook by seconds, so
  `GET orders/{slug}/` on a `pending_payment` order calls
  `retrieve_checkout_session()` and, when `payment_status == "paid"`, applies
  the same idempotent paid-transition (order `paid_pending_data`, artwork
  `sold`) before returning the summary; unpaid → `404` and the frontend
  retries/polls. Both paths (webhook + fallback) are idempotent, so whichever
  runs second is a no-op.
- Delivery POST validates required fields; only `paid_pending_data` orders
  accept data (409 otherwise) — the order slug is the capability token, and
  it is only exposed to the buyer via the success redirect.

### D7. Redirect URLs via `PUBLIC_SITE_URL`
- `settings.PUBLIC_SITE_URL = os.getenv("PUBLIC_SITE_URL", "")` alongside the
  existing Stripe env block. success_url =
  `{PUBLIC_SITE_URL}/compra-exitosa/?order={order_slug}` (frontend reads the
  query param, renders the form via `GET orders/{slug}/`); cancel_url =
  `{PUBLIC_SITE_URL}/compra-cancelada/`. Path literals owned here, page
  content owned by the frontend.
- Missing env → buy endpoint returns 503 before creating anything (fail-fast,
  admin-actionable).

### D8. Admin: orders-centric operator UI
- `ArtworkOrderAdmin` (Unfold, Spanish labels/help_texts per
  `docs/django-model-definitions.md` + `admin-spanish-labels` conventions):
  changelist with `status` filter + date drilldown, readonly
  Stripe/buyer/paid fields, delivery fieldsets; actions **Marcar enviada**
  (`data_complete→shipped`), **Marcar entregada** (`shipped→delivered`),
  **Liberar reserva** (`pending_payment→cancelled` + artwork release), each
  validating the source status and messaging on invalid transitions.
- Readonly `ArtworkOrder` inline (TabularInline, `max_num=0`-style readonly)
  on the Artwork change page so the operator sees an artwork's sale history
  without hunting the orders list.

### D9. Testing per the project contract
- Django-only (`venv/bin/python manage.py test`); `TestCase` +
  `unittest.mock.patch` on `stripe_client` functions (no network), mirroring
  the subscriptions test style. Suites: buy guards/race/throttle, webhook
  handlers (completed/expired/duplicate/refund-backstop/legacy-kind
  fallthrough), delivery transitions, admin actions, order-summary visibility.
- Manual E2E follows `docs/testing-stripe.md` (Stripe CLI bridge) — same
  recipe as subscriptions, trigger `checkout.session.completed`.

## Risks / Trade-offs

- **[USD on MX Stripe account]** Checkout in USD may be rejected
  (account currency support) → spike in test mode before release
  (`stripe.checkout.Session.create` with `usd`); buy endpoint maps Stripe
  creation failures to `502`, rolls back the reservation, and the frontend
  falls back to MXN. Documented in tasks as a pre-flight step.
- **[Async payment methods (OXXO/SPEI) handled]** For methods that settle
  asynchronously (OXXO, SPEI — plausible in the MXN market),
  `checkout.session.completed` can arrive with `payment_status="unpaid"` and
  the real confirmation arrives via `checkout.session.async_payment_succeeded`
  / `.async_payment_failed`, which ARE in the dispatch table (D3). The
  completed handler only transitions on `payment_status == "paid"`
  (unpaid sessions stay `pending_payment`, reservation holds); v1 still
  assumes mostly card payments, but OXXO/SPEI now resolve to paid or
  cancelled instead of sticking forever.
- **[Stripe call inside the buy transaction]** Lock hold time / partial
  failure modes → whole-tx rollback is safe; traffic is tiny; admin release
  action + expired-webhook cover stale states.
- **[Public order token in URL]** `?order=<slug>` leaks an unguessable token
  into browser history/logs → slug is uuid-hex, order data is low-sensitivity
  (artwork title + amount); acceptable.
- **[Stale reservations if webhooks are lost]** e.g. prod webhook misconfig →
  artwork stuck `reserved` → admin **Liberar reserva** plus external-cron
  `release_expired_orders` command (queries `pending_payment` with
  `session_expires_at` in the past → `cancelled` + artwork `available`,
  idempotent, logs counts); `session_expires_at` is stored on the order
  (drives same-buyer reuse and the reaper) — no in-process background worker.
- **[Refund leaves Stripe fees]** Backstop refunds don't recover processing
  fees → accepted; double-sale is already prevented upstream by D4.
- **[Manual refunds via Stripe Dashboard]** Operator-initiated refunds (buyer
  request, failed delivery) are done in the Stripe Dashboard, not via a
  dashboard admin action — out of scope for v1 by operator decision.
- **[Reconciliation via command]** `sync_orders_from_stripe` (read-only
  `retrieve_checkout_session` per `pending_payment` order, `--dry-run` flag)
  covers webhook loss / deploy downtime drift; mirrors the subscriptions
  `sync_from_stripe` convention. No Stripe list pagination needed — driven
  by local pending rows.
- **[currency snapshot drift]** Operator edits `price_usd` between buy-click
  and payment → order keeps the snapshot `amount`; Checkout charges the
  session's frozen amount. Correct by construction.
- **[same-buyer reuse forces original currency]** A buyer who re-clicks with
  a different currency preference inside the TTL gets the original session's
  currency → after the 30-min expiry they can retry with the other currency.
  Accepted (operator decision).

## Migration Plan

1. Pre-flight: verify USD Checkout in Stripe test mode (spike; record result
   in `docs/stripe-account-setup.md` or the task notes).
2. Deploy: migration adds `ArtworkOrder` (pure additive, no changes to
   existing tables); set `PUBLIC_SITE_URL` env; Stripe dashboard needs **no**
   new webhook endpoint (existing `/webhooks/stripe/` already receives
   checkout events).
3. Smoke: test-mode buy on one artwork → pay `4242…` → delivery form → admin
   actions; then expire path (`stripe trigger checkout.session.expired` or
   let session lapse).
4. Rollback: remove env var + `python manage.py migrate <app> <previous>`
   (additive table drop loses only sale rows); subscriptions path unaffected
   by construction.

## Open Questions

- Exact frontend paths: assumed `/compra-exitosa/` and `/compra-cancelada/`;
  frontend owner confirms before deploy (change is a constant + env var).
- Throttle rates: `20/hour` buy / `60/hour` orders are starting points;
  revisit if the frontend pre-warms sessions aggressively.
- Tracking number/courier field on `shipped` — omitted (Non-Goal) unless the
  operator asks; add a nullable column then.
