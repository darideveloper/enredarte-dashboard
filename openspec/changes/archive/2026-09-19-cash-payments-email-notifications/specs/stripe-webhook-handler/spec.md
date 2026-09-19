## MODIFIED Requirements

### Requirement: Correlation by stripe_customer_id and metadata
The system SHALL correlate Stripe events to local `ArtistSubscription` rows via `stripe_customer_id` first, and via `metadata.artist_id` (set on Checkout Session creation) for `checkout.session.completed` events that arrive before the customer id is known locally. The `customer` expanded-object form `{"id":...}` SHALL be unwrapped via `sget` where used. Rows with `payment_method="cash"` SHALL be excluded from correlation: when the matched row is a cash row, the handler SHALL log the event and make no mutation (cash state is operator-managed only).

#### Scenario: Checkout completion correlates via metadata
- **WHEN** Stripe delivers `checkout.session.completed` with `metadata.artist_id=42` and the artist already has a `pending` `ArtistSubscription`
- **THEN** the handler SHALL attach the Stripe `customer_id` (`cus_xxx`) and `subscription` id (`sub_xxx`) to that `ArtistSubscription` row.

#### Scenario: Event with no matching subscription
- **WHEN** Stripe delivers an event whose `customer_id` does not match any `ArtistSubscription`
- **THEN** the handler SHALL record the event in `StripeEvent` and SHALL NOT create or modify any subscription row.

#### Scenario: Event matching a cash row is ignored
- **WHEN** Stripe delivers any subscription/invoice event whose correlated row has `payment_method="cash"` (e.g. a recycled `cus_xxx` from a prior online history)
- **THEN** the handler SHALL record the event in `StripeEvent`, log the ignore with the artist id, and SHALL NOT modify the cash row or `Artist.is_active`.
