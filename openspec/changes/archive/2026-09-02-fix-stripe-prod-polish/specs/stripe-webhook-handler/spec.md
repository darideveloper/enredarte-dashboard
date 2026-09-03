## MODIFIED Requirements

### Requirement: Signed Stripe webhook endpoint
The system SHALL expose a single `POST /webhooks/stripe/` endpoint that accepts Stripe events. The endpoint MUST verify the `Stripe-Signature` header against the configured webhook secret before doing any work, and MUST be exempted from CSRF (`@csrf_exempt`).

#### Scenario: Valid signature accepted
- **WHEN** Stripe POSTs an event with a valid `Stripe-Signature` header
- **THEN** the endpoint SHALL parse the event, dispatch to its handler, and return HTTP 200 once the handler succeeds.

#### Scenario: Invalid signature rejected
- **WHEN** Stripe POSTs an event with an invalid `Stripe-Signature` header
- **THEN** the endpoint MUST return HTTP 400 and MUST NOT touch the database.

#### Scenario: Missing signature header
- **WHEN** a request arrives without a `Stripe-Signature` header
- **THEN** the endpoint MUST return HTTP 400 and MUST NOT touch the database.

### Requirement: Webhook idempotency via StripeEvent
The system SHALL persist every received Stripe event to a `StripeEvent` model keyed by the unique `event_id` from Stripe. Duplicate deliveries of the same `event_id` MUST be no-ops.

#### Scenario: First delivery of an event
- **WHEN** a webhook with `event_id=evt_aaa` arrives for the first time
- **THEN** the system SHALL create a `StripeEvent` row with `event_id="evt_aaa"`, dispatch the event, and mark `processed_at` upon success.

#### Scenario: Replayed delivery of an event
- **WHEN** a webhook with `event_id=evt_aaa` arrives a second time (Stripe replay or manual retry)
- **THEN** the endpoint SHALL return HTTP 200 without re-processing and without producing duplicate side effects on `ArtistSubscription` or `Artist.is_active`.

#### Scenario: Audit-only events still recorded
- **WHEN** a webhook arrives for an event type the system does not handle
- **THEN** the system SHALL still create a `StripeEvent` row with `error=""` (or empty), dispatch to a no-op handler, and return HTTP 200.

### Requirement: Atomic state update per webhook
The system SHALL dispatch each handled event inside a single Django `transaction.atomic()` block so that the `ArtistSubscription.upsert` and `Artist.is_active` update commit together. The `StripeEvent` row is created inside the same atomic block; any exception SHALL roll the entire transaction back including the `StripeEvent` row, the endpoint SHALL return `500` (so Stripe retries), and the retry SHALL be treated as a fresh run. The exception SHALL be logged via `logger.exception` with `event_id`/`event_type` for observability; `StripeEvent.error` is intentionally NOT persisted on crash (keeps retry clean and matches `tests.py:348` `assertFalse(StripeEvent.exists)`). Stripe SDK payload conversion SHALL use `event.to_dict(for_json=True)` fallback + `to_plain_dict` to handle `Decimal` fields.

#### Scenario: Handler crashes after upsert
- **WHEN** a handler raises an exception after writing to `ArtistSubscription` but before setting `Artist.is_active`
- **THEN** the database SHALL roll back the partial write, no `StripeEvent` row SHALL remain, `logger.exception` SHALL be called with the `event_id`, the endpoint SHALL return `500`, and Stripe SHALL retry. `StripeEvent.error` SHALL remain unused in this path (see `stripe-observability`).

#### Scenario: Stripe receives the retry
- **WHEN** Stripe retries the same `event_id` after the failed processing
- **THEN** the second delivery SHALL be treated as a fresh run (the previous transaction was rolled back).

### Requirement: Event-type dispatch table
The system SHALL dispatch events to one handler per Stripe event type. The handled types SHALL include at least: `checkout.session.completed`, `checkout.session.expired`, `customer.subscription.created`, `customer.subscription.updated`, `customer.subscription.deleted`, `invoice.payment_succeeded`, `invoice.payment_failed`. `checkout.session.completed` SHALL correlate via `metadata.artist_id`; `checkout.session.expired` SHALL clear the expired `signup_url`/`signup_url_expires_at` (if the session matches the stored URL) and SHALL NOT change `status` away from `pending` except to log.

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
- **WHEN** Stripe delivers `checkout.session.expired` for a session whose URL matches the stored `ArtistSubscription.signup_url` (or whose `metadata.artist_id` matches the artist)
- **THEN** the handler SHALL clear `signup_url`/`signup_url_expires_at` (or leave empty) and SHALL log `INFO` with the `artist_id`; `status` SHALL remain `pending` and no new `stripe_customer_id` SHALL be created.

### Requirement: Correlation by stripe_customer_id and metadata
The system SHALL correlate Stripe events to local `ArtistSubscription` rows via `stripe_customer_id` first, and via `metadata.artist_id` (set on Checkout Session creation) for `checkout.session.completed` events that arrive before the customer id is known locally. The `customer` expanded-object form `{"id":...}` SHALL be unwrapped via `sget` where used.

#### Scenario: Checkout completion correlates via metadata
- **WHEN** Stripe delivers `checkout.session.completed` with `metadata.artist_id=42` and the artist already has a `pending` `ArtistSubscription`
- **THEN** the handler SHALL attach the Stripe `customer_id` (`cus_xxx`) and `subscription` id (`sub_xxx`) to that `ArtistSubscription` row.

#### Scenario: Event with no matching subscription
- **WHEN** Stripe delivers an event whose `customer_id` does not match any `ArtistSubscription`
- **THEN** the handler SHALL record the event in `StripeEvent` and SHALL NOT create or modify any subscription row.

### Requirement: StripeEvent audit log model fields
The system SHALL provide a `StripeEvent` model with at least these fields (each with `verbose_name`): `event_id` (unique, max 120), `event_type` (max 80), `received_at` (auto_now_add), `processed_at` (nullable), `payload` (JSON), `error` (text, blank). The model MUST have `verbose_name` / `verbose_name_plural` and a content-based `__str__` returning the event type truncated. Payload storage SHALL use `to_plain_dict(for_json=True)` + `_convert_decimals` so `Decimal` fields are `str` and `JSONField` never raises `TypeError: Decimal is not JSON serializable`.

#### Scenario: Admin browses the audit log
- **WHEN** an administrator opens the "Eventos de Stripe" admin
- **THEN** rows SHALL be ordered by `received_at` desc, SHALL show `event_type`, a short prefix of `event_id`, and `processed_at` (or `error` if a processing failure occurred).

#### Scenario: Unique constraint protects against duplicates
- **WHEN** two webhooks with the same `event_id` arrive concurrently
- **THEN** the database SHALL accept only one row and the losing handler SHALL treat the duplicate as already processed.

