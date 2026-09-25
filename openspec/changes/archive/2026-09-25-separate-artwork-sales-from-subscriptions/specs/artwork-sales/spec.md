## ADDED Requirements

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
