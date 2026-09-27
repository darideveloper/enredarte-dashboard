## ADDED Requirements

### Requirement: Artwork webhook branches delegated to artworks

The system SHALL implement artwork-branch webhook logic (`checkout.session.completed` paid-transition with double-sale refund backstop, `checkout.session.expired` release, `async_payment_succeeded` / `async_payment_failed`) in `artworks/order_webhooks.py` as pure functions taking the order and the session dict; `subscriptions/webhooks.py` SHALL keep signature verification, the `StripeEvent` insert (now `core.models.StripeEvent`), the single atomic block, and the `HANDLERS` dispatch table, delegating artwork sessions (detected via `metadata.kind == "artwork_order"`) to the artworks functions. The endpoint URL (`POST /webhooks/stripe/`), idempotency-via-unique-`event_id`, rollback-on-handler-crash (500 → Stripe retry), duplicate-delivery 200, and cash-row guards SHALL NOT change.

#### Scenario: Paid artwork session completes via delegation

- **WHEN** `checkout.session.completed` arrives with `metadata.kind == "artwork_order"` and `payment_status == "paid"`
- **THEN** the order SHALL transition `pending_payment → paid_pending_data`, the artwork SHALL become `sold`, and `send_sale_paid` SHALL fire once via `transaction.on_commit`, exactly as today.

#### Scenario: Single URL preserved

- **WHEN** Stripe posts any supported event type to `POST /webhooks/stripe/`
- **THEN** routing SHALL happen internally by event type + metadata, with no second webhook URL registered anywhere.
