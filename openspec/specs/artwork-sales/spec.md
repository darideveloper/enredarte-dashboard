# Artwork Sales Specification

## Purpose

This specification defines the end-to-end purchase of unique artworks via Stripe one-off payments: public buy / order-summary / delivery endpoints, the `ArtworkOrder` sale lifecycle (`pending_payment` → `paid_pending_data` → `data_complete` → `shipped` → `delivered`, with `cancelled` / `refunded` exits), reservation & release handling, the double-sale refund backstop, async payment (OXXO/SPEI) confirmation, the `release_expired_orders` / `sync_orders_from_stripe` management commands, and the operator admin UI.

## Requirements


### Requirement: Public buy endpoint reserves the artwork and creates a Checkout Session
The system SHALL expose `POST /api/artworks/artworks/{slug}/buy/` as a public (unauthenticated) endpoint that accepts `{"currency": "mxn" | "usd", "email": <buyer email>}` (the buyer email identifies the reservation owner; the frontend collects it on the buy screen). The endpoint SHALL be protected by a scoped DRF `ScopedRateThrottle`. For an active artwork, the endpoint SHALL atomically (`select_for_update`) verify `status == "available"`, transition the artwork to `reserved`, create an `ArtworkOrder` with `status="pending_payment"`, snapshot the currency and price (`price_mxn` / `price_usd`), store the buyer email (normalized lowercase) as `buyer_email`, and create a Stripe Checkout Session (`mode="payment"`, inline `price_data`, `customer_email` = buyer email, `expires_at` = now + 30 minutes, `metadata` = `{"kind": "artwork_order", "order": <order_slug>}`), storing `checkout_url` and `session_expires_at` on the order and returning `{"checkout_url": ...}`. When the artwork is `reserved` with stale `pending_payment` order(s) (`session_expires_at` in the past), the endpoint SHALL reconcile each stale order newest-first against Stripe (via `retrieve_checkout_session`, Stripe fetch outside the row lock, re-verify + mutate inside `select_for_update`, stopping at the first paid-transition) before refusing: a hold whose session reports `status == "expired"` with `payment_status != "paid"` SHALL be released (`cancel_order`) and the request SHALL proceed as a fresh `available` sale; a hold reporting `payment_status == "paid"` SHALL be completed (paid-transition, artwork → `sold`, including the double-sale refund backstop) and the request SHALL be refused with `409` and message `"Obra no disponible."`; a hold whose session is still `open` + unpaid, or that is unverifiable (Stripe error/unknown shape, or `session_expires_at=None`), SHALL keep the reservation and return `409` as today.

#### Scenario: Successful buy (MXN)
- **WHEN** `POST /api/artworks/artworks/{slug}/buy/` is called with `{"currency": "mxn", "email": "a@b.com"}` for an active artwork with `status="available"`
- **THEN** the response SHALL be `201` with a `checkout_url`, the artwork SHALL be `reserved`, and an `ArtworkOrder` with `status="pending_payment"`, `currency="mxn"`, `buyer_email="a@b.com"`, and `amount == artwork.price_mxn` SHALL exist.

#### Scenario: Successful buy (USD)
- **WHEN** the endpoint is called with `{"currency": "usd", "email": "a@b.com"}`
- **THEN** the session SHALL be created with `amount == artwork.price_usd` and `currency="usd"`.

#### Scenario: Artwork not available
- **WHEN** the endpoint is called for an artwork whose `status` is not `available` (e.g. `sold`, `reserved`, `on_loan`, `not_available`)
- **THEN** the response SHALL be `409 Conflict` with the project error format, no order SHALL be created, and the artwork status SHALL be unchanged.

#### Scenario: Artwork inactive or unknown slug
- **WHEN** the endpoint is called with an unknown slug or an artwork with `is_active=False`
- **THEN** the response SHALL be `404 Not Found`.

#### Scenario: Invalid currency or missing buyer email
- **WHEN** the endpoint is called with a currency other than `mxn` or `usd`, or without a valid email
- **THEN** the response SHALL be `400` and no order SHALL be created.

#### Scenario: Repeat buy by the same buyer reuses the live session
- **WHEN** a buy request arrives for an artwork whose `pending_payment` order has a live session (`session_expires_at` in the future) and the request email matches `order.buyer_email` (case-insensitively)
- **THEN** the endpoint SHALL return `200` with the existing stored `checkout_url` without creating a new session, a new order, or changing the artwork status.

#### Scenario: Repeat buy by a different buyer
- **WHEN** a buy request arrives for a reserved artwork whose pending order has a live session and the request email does not match `order.buyer_email`
- **THEN** the response SHALL be `409 Conflict` with a reservation-in-progress message, and no new order SHALL be created.

#### Scenario: Stale hold verified expired is released and sale proceeds
- **WHEN** a buy request arrives for a `reserved` artwork with stale `pending_payment` order(s) and Stripe reports the newest stale session with `status == "expired"` and `payment_status != "paid"`
- **THEN** the stale order(s) SHALL become `cancelled` (artwork → `available`) and the request SHALL proceed as a fresh sale with `201` and a new `checkout_url`, computed from the re-read (post-transition) artwork row.

#### Scenario: Stale hold verified paid becomes sold
- **WHEN** a buy request arrives for a `reserved` artwork whose stale `pending_payment` order reports `payment_status == "paid"` at Stripe
- **THEN** the order SHALL transition to `paid_pending_data` (artwork → `sold`, including the double-sale refund backstop) and the buy request SHALL return `409 Conflict` with message `"Obra no disponible."` and no new order created.

#### Scenario: Stale-local-expiry but Stripe session still open keeps the reservation
- **WHEN** a buy request arrives for a `reserved` artwork with a past `session_expires_at` but Stripe reports the session still `open` and unpaid (e.g. async OXXO/SPEI settling)
- **THEN** the response SHALL be `409 Conflict`, the order SHALL remain `pending_payment`, and the artwork SHALL remain `reserved`.

#### Scenario: Stale hold unverifiable keeps the reservation
- **WHEN** a buy request arrives for a `reserved` artwork with a past `session_expires_at` but Stripe is unreachable, returns an unknown shape, or the order has `session_expires_at=None`
- **THEN** the response SHALL be `409 Conflict`, the order SHALL remain `pending_payment`, and the artwork SHALL remain `reserved`.

#### Scenario: Concurrent buys race
- **WHEN** two buy requests for the same available artwork race
- **THEN** exactly one SHALL win the reservation and return a `checkout_url`; the other SHALL receive `409 Conflict`.

#### Scenario: Rate throttled
- **WHEN** an anonymous client exceeds the scoped throttle rate on the buy endpoint
- **THEN** the response SHALL be `429 Too Many Requests`.

### Requirement: Checkout Session URLs point at the public site
The buy endpoint SHALL build the Checkout Session `success_url` from `settings.PUBLIC_SITE_URL` as `{PUBLIC_SITE_URL}/compra-exitosa/?order={order_slug}` and `cancel_url` as `{PUBLIC_SITE_URL}/compra-cancelada/`.

#### Scenario: Success redirect target
- **WHEN** a Checkout Session is created for an order
- **THEN** `success_url` SHALL contain the public site URL and the order slug as a query parameter.

#### Scenario: Missing PUBLIC_SITE_URL
- **WHEN** `PUBLIC_SITE_URL` is not configured
- **THEN** the buy endpoint SHALL return `503` with an admin-actionable error and SHALL NOT create an order or reserve the artwork.

### Requirement: Public order summary endpoint with webhook-race fallback
The system SHALL expose `GET /api/artworks/orders/{slug}/` as a public endpoint returning the order summary (`status`, `currency`, `amount`, `paid_at`, artwork title/image/artist) for the frontend success page. The endpoint SHALL be protected by a scoped DRF `ScopedRateThrottle`. When the order is still `pending_payment` (the success redirect can arrive before the `checkout.session.completed` webhook), the endpoint SHALL verify the stored Checkout Session against Stripe; if its `payment_status` is `paid`, it SHALL apply the same idempotent paid-transition as the webhook handler and return the summary. Unknown slugs and orders that remain unpaid (or are `cancelled` / `refunded`) SHALL return `404`.

#### Scenario: Paid order summary
- **WHEN** the endpoint is called with the slug of an order in `paid_pending_data`, `data_complete`, `shipped`, or `delivered`
- **THEN** the response SHALL be `200` with the order summary including the artwork data and buyer-facing amounts.

#### Scenario: Redirect beats the webhook, Stripe says paid
- **WHEN** the endpoint is called for a `pending_payment` order whose Stripe session reports `payment_status == "paid"`
- **THEN** the order SHALL transition to `paid_pending_data` (artwork → `sold`, payment intent/buyer/paid_at stored) and the response SHALL be `200` with the summary.

#### Scenario: Redirect beats the webhook, Stripe says unpaid
- **WHEN** the endpoint is called for a `pending_payment` order whose Stripe session is not paid
- **THEN** the response SHALL be `404 Not Found` and no state SHALL change (the frontend should retry/poll).

#### Scenario: Unpaid or unknown order hidden
- **WHEN** the endpoint is called with an unknown slug, or an order in `cancelled` / `refunded`
- **THEN** the response SHALL be `404 Not Found`.

### Requirement: Public delivery submission endpoint
The system SHALL expose `POST /api/artworks/orders/{slug}/delivery/` as a public endpoint that saves delivery info only when the order is `paid_pending_data`, transitioning it to `data_complete`. The endpoint SHALL be protected by a scoped DRF `ScopedRateThrottle`. Required fields: `receiver_name`, `receiver_phone`, `country`, `state`, `city`, `postal_code`, `neighborhood`, `street`, `exterior_number`. Optional fields: `interior_number`, `between_street_1`, `between_street_2`, `reference`, `delivery_notes`. Invalid state transitions SHALL return `409`.

#### Scenario: Delivery info accepted
- **WHEN** the endpoint is called with all required fields for an order in `paid_pending_data`
- **THEN** the response SHALL be `200`, the delivery fields SHALL be persisted, and the order SHALL become `data_complete`.

#### Scenario: Order not awaiting delivery data
- **WHEN** the endpoint is called for an order not in `paid_pending_data` (e.g. `pending_payment`, `data_complete`)
- **THEN** the response SHALL be `409 Conflict` and no fields SHALL be saved.

#### Scenario: Missing required fields
- **WHEN** a required delivery field is absent or blank
- **THEN** the response SHALL be `400` with field-level errors and the order SHALL remain `paid_pending_data`.

### Requirement: Reservation release on expiry
The system SHALL release the reservation when a checkout is never completed: on `checkout.session.expired` (or `checkout.session.async_payment_failed`) for an artwork order, the order SHALL become `cancelled` and the artwork SHALL return to `available` — only if the order is still `pending_payment`. The admin SHALL provide a manual **Liberar reserva** action that performs the same transition for stale reservations (webhook lost / local dev). The system SHALL also provide a `release_expired_orders` management command (designed for an external cron service) that transitions `pending_payment` orders with `session_expires_at` in the past to `cancelled` (set `cancelled_at`) and returns their artworks to `available`; the command SHALL be idempotent and SHALL log counts.

#### Scenario: Expired orders reaper command
- **WHEN** `release_expired_orders` runs with a `pending_payment` order whose `session_expires_at` is in the past
- **THEN** the order SHALL become `cancelled` with `cancelled_at` set and the artwork SHALL become `available`.

#### Scenario: Reaper skips live sessions
- **WHEN** `release_expired_orders` runs with a `pending_payment` order whose `session_expires_at` is still in the future, or an order past `pending_payment`
- **THEN** the order and artwork SHALL be unchanged.

### Requirement: Reconciliation command for order drift
The system SHALL provide a `sync_orders_from_stripe` management command (read-only Stripe reads, `--dry-run` flag) that reconciles local `ArtworkOrder` rows against Stripe: for each `pending_payment` order it SHALL retrieve the stored Checkout Session via `retrieve_checkout_session`; if Stripe reports `payment_status == "paid"` it SHALL apply the idempotent paid-transition, if the session is expired it SHALL cancel/release. The command SHALL log per-order actions and a summary count and SHALL never create new orders.

#### Scenario: Reconcile finds paid order
- **WHEN** `sync_orders_from_stripe` runs with a `pending_payment` order whose Stripe session reports `payment_status == "paid"`
- **THEN** the order SHALL become `paid_pending_data` and the artwork SHALL become `sold`.

#### Scenario: Dry run changes nothing
- **WHEN** `sync_orders_from_stripe --dry-run` runs
- **THEN** no order or artwork SHALL change and the log SHALL report would-be actions.

#### Scenario: Checkout expired webhook
- **WHEN** `checkout.session.expired` arrives with `metadata.kind="artwork_order"` for a `pending_payment` order
- **THEN** the order SHALL become `cancelled`, its `cancelled_at` SHALL be set, and the artwork SHALL be `available` again.

#### Scenario: Expired after payment already processed
- **WHEN** `checkout.session.expired` arrives for an order already past `pending_payment`
- **THEN** the order and artwork SHALL be unchanged.

#### Scenario: Manual release
- **WHEN** an operator runs the **Liberar reserva** action on a `pending_payment` order in the admin
- **THEN** the order SHALL become `cancelled` and the artwork SHALL return to `available`.

### Requirement: Auto-refund backstop for double-sale
If `checkout.session.completed` arrives for an artwork order whose artwork is no longer reserved by that order (already `sold` by another order, `reserved` by a later session, or not available), the system SHALL mark the order `refunded` and SHALL issue a Stripe refund for the session's payment intent, logging the compensation. If refunding fails, the error SHALL be logged via `logger.exception`, the handler SHALL raise so the endpoint returns `500` and Stripe retries, and no partial order state SHALL persist (atomic rollback).

#### Scenario: Payment completes for already-sold artwork
- **WHEN** `checkout.session.completed` arrives for an order whose artwork is `sold`
- **THEN** the order SHALL become `refunded` and a Stripe refund SHALL be created for the payment intent.

#### Scenario: Refund API failure
- **WHEN** the Stripe refund call raises
- **THEN** the exception SHALL be logged, the endpoint SHALL return `500` so Stripe retries, and no partial order state SHALL persist.

### Requirement: ArtworkOrder model mirrors the sale lifecycle
The system SHALL persist each sale as an `ArtworkOrder` (artworks app) with: artwork FK (`PROTECT`), uuid-hex slug token, `status` (`pending_payment`, `paid_pending_data`, `data_complete`, `shipped`, `delivered`, `cancelled`, `refunded`), `currency` (`mxn` | `usd`), `amount` snapshot, `stripe_checkout_session_id`, `checkout_url`, `session_expires_at`, `stripe_payment_intent_id`, `buyer_email` (captured from the buy request, normalized lowercase), `buyer_name` (from Stripe), `paid_at` / `cancelled_at` timestamps, and flat delivery fields. The artwork-order completed handler SHALL only transition an order to `paid_pending_data` when the session's `payment_status` is `paid` (guards asynchronous payment methods). The model SHALL follow project conventions: Spanish `verbose_name` on the model and every field, `help_text` on non-obvious fields, content-based `__str__`.

#### Scenario: Model conventions
- **WHEN** `ArtworkOrder` is inspected in the Django admin
- **THEN** it SHALL display Spanish `verbose_name` / `verbose_name_plural`, Spanish field labels with help texts, and a content-based `__str__` (artwork title + status).

#### Scenario: Order row on paid webhook
- **WHEN** `checkout.session.completed` for an artwork order is processed and the session reports `payment_status == "paid"`
- **THEN** the order SHALL store `stripe_payment_intent_id`, `buyer_email`, `buyer_name`, `paid_at`, and `status="paid_pending_data"`, and the artwork SHALL be `sold`.

#### Scenario: Completed event with unpaid session is ignored
- **WHEN** `checkout.session.completed` arrives with `payment_status != "paid"` (e.g. asynchronous payment method still settling)
- **THEN** the order SHALL remain `pending_payment`, the artwork SHALL remain `reserved`, and the event SHALL still be recorded in `StripeEvent` with HTTP `200` (final confirmation arrives later via `checkout.session.async_payment_succeeded` / `async_payment_failed`).

### Requirement: Async payment confirmation for artwork orders
The system SHALL handle `checkout.session.async_payment_succeeded` and `checkout.session.async_payment_failed` for sessions with `metadata.kind="artwork_order"` (correlating via `metadata.order`). On `async_payment_succeeded` for a `pending_payment` order the system SHALL apply the same idempotent paid-transition as the completed handler (store payment intent/buyer/paid_at → `paid_pending_data`, artwork → `sold`), including the double-sale refund backstop. On `async_payment_failed` for a `pending_payment` order the system SHALL transition the order to `cancelled` (set `cancelled_at`) and return the artwork to `available`. Events for orders past `pending_payment` SHALL be no-ops recorded with HTTP `200`.

#### Scenario: Async payment succeeds
- **WHEN** `checkout.session.async_payment_succeeded` arrives for a `pending_payment` artwork order
- **THEN** the order SHALL become `paid_pending_data` and the artwork SHALL become `sold`.

#### Scenario: Async payment fails
- **WHEN** `checkout.session.async_payment_failed` arrives for a `pending_payment` artwork order
- **THEN** the order SHALL become `cancelled` with `cancelled_at` set and the artwork SHALL become `available`.

#### Scenario: Async event after terminal state is ignored
- **WHEN** an async payment event arrives for an order already past `pending_payment`
- **THEN** the order and artwork SHALL be unchanged and the event SHALL be recorded with HTTP `200`.

### Requirement: Admin tracks shipment after delivery data
The Django admin SHALL present `ArtworkOrder` with a changelist filterable by status, readonly Stripe fields, a delivery-info fieldset, and admin actions **Marcar enviada** (`data_complete → shipped`) and **Marcar entregada** (`shipped → delivered`). The Artwork change page SHALL show a readonly orders inline. Invalid transitions SHALL be rejected by the admin actions.

#### Scenario: Mark shipped
- **WHEN** an operator runs **Marcar enviada** on a `data_complete` order
- **THEN** the order SHALL become `shipped`.

#### Scenario: Mark delivered
- **WHEN** an operator runs **Marcar entregada** on a `shipped` order
- **THEN** the order SHALL become `delivered`.

#### Scenario: Invalid transition rejected
- **WHEN** **Marcar enviada** is attempted on a `pending_payment` order
- **THEN** the admin SHALL show an error message and the status SHALL be unchanged.

#### Scenario: Orders inline on artwork page
- **WHEN** an Artwork with orders is opened in the admin
- **THEN** a readonly orders inline SHALL list its orders with status and amounts.

### Requirement: USD checkout account readiness
The buy endpoint SHALL degrade gracefully if USD payments are not enabled on the Stripe account: when session creation for `usd` fails, the error SHALL be logged and surfaced as a `502` response, the order SHALL NOT be created, and the artwork SHALL NOT remain reserved. The system SHALL document a test-mode verification spike before production use of `usd`.

#### Scenario: USD not enabled on account
- **WHEN** Stripe rejects a `usd` Checkout Session creation (e.g. currency not supported)
- **THEN** the response SHALL be `502`, no order SHALL exist, and the artwork SHALL be `available` again.

### Requirement: Sale Stripe client owned by artworks

The system SHALL provide `artworks/stripe_orders.py` exposing `create_artwork_checkout_session`, `retrieve_checkout_session`, and `create_refund` with signatures and Stripe behavior identical to today (`mode="payment"`, inline `price_data`, `customer_email` lock, 30-minute `expires_at`, `metadata {"kind": "artwork_order", "order": slug}`, full refunds). `subscriptions/services/stripe_client.py` SHALL NOT contain these three functions after the change. `artworks/views.py` (`buy`, `OrderSummaryView`), `artworks/services.py` (reconcile + double-sale backstop), `artworks/management/commands/sync_orders_from_stripe.py`, and the sale webhook path SHALL import them from `artworks.stripe_orders`. The `ArtworkOrder` lifecycle, reservation semantics, throttles, and public REST paths SHALL NOT change.

#### Scenario: Buy creates payment session from artworks module

- **WHEN** `POST /api/artworks/artworks/{slug}/buy/` reserves an available artwork
- **THEN** the Checkout Session SHALL be created via `artworks.stripe_orders.create_artwork_checkout_session` with the same `price_data`, `customer_email`, expiry, and metadata as today, and the response SHALL be `201` with `checkout_url`.

#### Scenario: Order summary paid fallback uses artworks client

- **WHEN** `GET /api/artworks/orders/{slug}/` finds a `pending_payment` order whose Stripe session reports `payment_status == "paid"`
- **THEN** the verify call SHALL use `artworks.stripe_orders.retrieve_checkout_session`, the paid-transition SHALL apply, and the response SHALL be the order summary.

#### Scenario: Double-sale refund uses artworks client

- **WHEN** a paid session completes for an artwork already sold by another order
- **THEN** the order SHALL become `refunded` and the refund SHALL be created via `artworks.stripe_orders.create_refund`.
