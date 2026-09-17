# Proposal: add-artwork-stripe-sales

## Why

The dashboard today only sells subscriptions; the actual product — unique
artworks — has no purchase path. The public catalog API already exposes
artworks with prices (`price_mxn` / `price_usd`), so the frontend can render
them, but there is no way for a visitor to buy one. This change adds a
one-off-payment sales flow on top of the existing Stripe infrastructure
(Checkout Sessions, signed webhooks, `StripeEvent` idempotency) so visitors can
buy artworks end-to-end and the operator can manage each sale from the admin.

## What Changes

- New `ArtworkOrder` model (artworks app) capturing the full sale lifecycle:
  `pending_payment → paid_pending_data → data_complete → shipped → delivered`,
  with `cancelled` / `refunded` side exits, currency + amount snapshot, Stripe
  session/payment-intent ids, buyer identity from Stripe, and flat delivery
  fields (Mexican addressing: colonia, entre calles, referencias).
- New public (unauthenticated, throttled) purchase API under `/api/artworks/`:
  - `POST artworks/{slug}/buy/` — accepts `{"currency": "mxn" | "usd", "email":
    <buyer email>}` (the frontend collects the buyer email on the buy screen).
    Creates the order, reserves the artwork (`available → reserved`), creates
    a `mode=payment` Checkout Session (inline `price_data`, 30-min expiry,
    `customer_email` locked to the request email, `metadata.kind="artwork_order"`),
    returns `{checkout_url}`. A repeat buy with the **same email** while the
    session is live returns the existing `checkout_url` (no double
    reservation); a **different email** gets `409` (reservation in progress).
  - `GET orders/{slug}/` — order summary for the frontend success page.
  - `POST orders/{slug}/delivery/` — accepts delivery info when the order is
    `paid_pending_data`, transitions it to `data_complete`.
- Concurrency guard: `select_for_update` on the artwork row so two simultaneous
  buyers cannot both reserve; auto-release on `checkout.session.expired` and
  `checkout.session.async_payment_failed`, plus a `release_expired_orders`
  management command for an external cron to recover stale reservations and
  a `sync_orders_from_stripe` command to reconcile drift.
- Backstop for double-sale: if a completed Checkout arrives for an artwork
  already sold, the second payment intent is refunded automatically.
- Webhook dispatch extended: `checkout.session.completed` / `.expired` /
  `.async_payment_succeeded` / `.async_payment_failed` now route on
  `metadata.kind` (`kind="artwork_order"` → order handlers; absence of
  `kind` → existing subscription behavior unchanged). Async methods
  (OXXO/SPEI) resolve via `async_payment_*` instead of sticking in
  `pending_payment`.
- `subscriptions/services/stripe_client.py` (the only module importing
  `stripe`) gains `create_artwork_checkout_session()`,
  `retrieve_checkout_session()`, `create_refund()`.
- New `PUBLIC_SITE_URL` env var; success/cancel URLs point at the external
  frontend (`/compra-exitosa/?order=<slug>`, `/compra-cancelada/`).
- New Django admin: `ArtworkOrder` changelist + change form (Spanish labels,
  readonly Stripe fields, delivery fieldsets) with actions **Marcar enviada**,
  **Marcar entregada**, **Liberar reserva**; readonly orders inline on the
  Artwork change page.

## Capabilities

### New Capabilities

- `artwork-sales`: End-to-end purchase of unique artworks — public buy /
  order-summary / delivery endpoints, reservation & release lifecycle,
  order model + status machine, shipped/delivered admin tracking, admin UI.

### Modified Capabilities

- `artworks-rest-api`: The "all endpoints require authentication" requirement
  gains an explicit exemption for the public sales endpoints introduced by
  `artwork-sales` (they are unauthenticated by design, protected by unguessable
  order tokens + scoped rate throttling).
- `stripe-webhook-handler`: The event-type dispatch requirement is extended so
  `checkout.session.completed`, `checkout.session.expired`,
  `checkout.session.async_payment_succeeded`, and
  `checkout.session.async_payment_failed` route on `metadata.kind`, adding
  the `artwork_order` handlers (order paid → sold; expired/failed →
  release reservation; async success → paid) plus the auto-refund backstop
  when payment completes for an artwork that is no longer
  reserved/available. Existing `metadata.artist_id` subscription behavior is
  unchanged.

## Impact

- **Code**: `artworks/models.py` (+`ArtworkOrder`), `artworks/serializers.py`,
  `artworks/views.py`, `artworks/urls.py`, `artworks/admin.py`,
  `subscriptions/services/stripe_client.py`, `subscriptions/webhooks.py`,
  `project/settings.py` (`PUBLIC_SITE_URL`), new migration(s).
- **APIs**: 3 new public endpoints under `/api/artworks/`; no changes to
  existing read-only endpoints or their contracts.
- **Stripe**: same account/keys as subscriptions; new webhook events only on
  the existing endpoint (no new endpoint, no new secret). One pre-flight spike:
  verify USD Checkout works on the MX-based account in test mode; if not, the
  buy endpoint rejects `usd` gracefully until enabled.
- **Frontend (external repo)**: consumes `{checkout_url}`, hosts
  `/compra-exitosa/` and `/compra-cancelada/`, posts delivery data.
- **No dependency changes** (stripe SDK v15 already installed).
