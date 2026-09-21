## MODIFIED Requirements

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
