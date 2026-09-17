# stripe-webhook-handler Delta Spec

## MODIFIED Requirements

### Requirement: Event-type dispatch table
The system SHALL dispatch events to one handler per Stripe event type. The handled types SHALL include at least: `checkout.session.completed`, `checkout.session.expired`, `checkout.session.async_payment_succeeded`, `checkout.session.async_payment_failed`, `customer.subscription.created`, `customer.subscription.updated`, `customer.subscription.deleted`, `invoice.payment_succeeded`, `invoice.payment_failed`. Checkout handlers SHALL route on `metadata.kind`: sessions without `kind` (or `kind="artist_subscription"`) keep the legacy subscription behavior — `checkout.session.completed` correlates via `metadata.artist_id`, `checkout.session.expired` clears the expired `signup_url`/`signup_url_expires_at` (if the session matches the stored URL) and SHALL NOT change `status` away from `pending` except to log. Sessions with `kind="artwork_order"` SHALL dispatch to the artwork-order handlers defined by the `artwork-sales` capability (correlating via `metadata.order`). Async payment events without `kind="artwork_order"` SHALL be recorded with HTTP `200` and SHALL NOT mutate any subscription.

#### Scenario: Subscription created event
- **WHEN** Stripe delivers `customer.subscription.created` for a customer linked to a known `ArtistSubscription`
- **THEN** the handler SHALL set `status="active"`, persist `stripe_subscription_id`, set `current_period_end`, run `compute_is_active`, persist its result to `Artist.is_active`, and clear `signup_url` / `signup_url_expires_at` (sign-up flow is complete).

#### Scenario: Subscription deleted event
- **WHEN** Stripe delivers `customer.subscription.deleted` for a known `ArtistSubscription`
- **THEN** the handler SHALL set `status="canceled"` and call `compute_is_active`, persisting the resulting `Artist.is_active=False`.

#### Scenario: Invoice payment failed event
- **WHEN** Stripe delivers `invoice.payment_failed` for a known `ArtistSubscription`
- **THEN** the handler SHALL set `status="past_due"`. The artist SHALL remain visible while `current_period_end + grace_period_days` is in the future and SHALL be flipped to inactive on the next event that crosses the boundary.

#### Scenario: Invoice payment succeeded event
- **WHEN** Stripe delivers `invoice.payment_succeeded` for a known recurring invoice
- **THEN** the handler SHALL set `status="active"` and SHALL refresh `current_period_end` **only if** the invoice's `lines.data[0].period.end` is non-null (guard `if period_end is not None: set`, otherwise keep existing `current_period_end`).

#### Scenario: Checkout session expired clears link
- **WHEN** Stripe delivers `checkout.session.expired` for a subscription-mode session whose URL matches the stored `ArtistSubscription.signup_url` (or whose `metadata.artist_id` matches the artist)
- **THEN** the handler SHALL clear `signup_url`/`signup_url_expires_at` (or leave empty) and SHALL log `INFO` with the `artist_id`; `status` SHALL remain `pending` and no new `stripe_customer_id` SHALL be created.

#### Scenario: Artwork order checkout completed routes to order handler
- **WHEN** Stripe delivers `checkout.session.completed` for a session with `metadata.kind="artwork_order"` and `metadata.order=<order_slug>`
- **THEN** the handler SHALL process the artwork order (order → `paid_pending_data`, artwork → `sold`, store payment intent + buyer identity) per the `artwork-sales` capability, and the subscription handler path SHALL NOT run for this event.

#### Scenario: Artwork order checkout expired routes to release handler
- **WHEN** Stripe delivers `checkout.session.expired` for a session with `metadata.kind="artwork_order"`
- **THEN** the handler SHALL release the reservation per the `artwork-sales` capability (order → `cancelled`, artwork → `available`, only from `pending_payment`), and the subscription handler path SHALL NOT run for this event.

#### Scenario: Artwork async payment succeeded routes to paid handler
- **WHEN** Stripe delivers `checkout.session.async_payment_succeeded` for a session with `metadata.kind="artwork_order"` and `metadata.order=<order_slug>`
- **THEN** the handler SHALL apply the paid-transition per the `artwork-sales` capability (order → `paid_pending_data`, artwork → `sold`), and the subscription handler path SHALL NOT run for this event.

#### Scenario: Artwork async payment failed routes to cancel handler
- **WHEN** Stripe delivers `checkout.session.async_payment_failed` for a session with `metadata.kind="artwork_order"` and `metadata.order=<order_slug>`
- **THEN** the handler SHALL cancel the pending order per the `artwork-sales` capability (order → `cancelled`, artwork → `available`, only from `pending_payment`), and the subscription handler path SHALL NOT run for this event.

#### Scenario: Unknown kind falls through safely
- **WHEN** a checkout event arrives with unrecognized `metadata.kind`
- **THEN** the event SHALL still be recorded in `StripeEvent`, return HTTP `200`, and SHALL NOT mutate any subscription or order.
