## MODIFIED Requirements

### Requirement: Generate subscription link action
The system SHALL provide a "Generar link de suscripción" changeform action on the Artist admin change page that creates a Stripe customer and checkout session when no subscription link has been generated yet. The action SHALL be visible only when the artist has no `signup_url` at all (no subscription or empty `signup_url`) AND the artist is not on the cash path (no cash `pending`/`active` row). Direct execution for a cash `pending`/`active` artist (via URL) is refused at the Unfold permission boundary (403) without mutation or email; the method additionally keeps a defensive `messages.error("Este artista paga en efectivo. Esta acción de Stripe no aplica.")` guard. When the stored `stripe_customer_id` is missing or deleted in Stripe (a stale-customer `StripeError` on the checkout call), the system SHALL clear the stale `stripe_customer_id`, create a fresh customer, and retry the checkout session once before falling through to the generic error path. When the stored `BillingPlan.stripe_price_id` is empty, or when the checkout raises a stale price/product error (a `resource_missing` `InvalidRequestError` referencing the stored `price`/`product`/`price_xxx`/`prod_xxx`, e.g. after a Stripe account switch or deleted/archived price), the system SHALL first regenerate the product/price via the `auto-price-regeneration` capability (`plan_sync.ensure_stripe_price`) and retry the checkout session once. For any other `StripeError` (network, auth, rate-limit) the system SHALL NOT return `500`; it SHALL `logger.warning` with the `artist_id` and error, show `messages.error` with prefix `Stripe no respondió` (e.g. `f"Stripe no respondió: {e}"`), and redirect `302` to the change form without persisting a partial link.

#### Scenario: Generate link for artist without a link
- **WHEN** an administrator opens an Artist change form and no subscription link exists (no subscription or empty `signup_url`)
- **THEN** the "Generar link de suscripción" action SHALL be shown and, when clicked, SHALL create a Stripe customer (if needed), create a checkout session, store the `signup_url` and `signup_url_expires_at`, set `status` to `PENDING`, and redirect back to the change form

#### Scenario: Generate link blocked by missing email
- **WHEN** an administrator clicks "Generar link de suscripción" for an artist with no email address
- **THEN** the system SHALL display an error message and redirect back to the change form without creating a subscription

#### Scenario: Generate link auto-creates price on a fresh database
- **WHEN** an administrator clicks "Generar link de suscripción" and `BillingPlan.stripe_price_id` is empty (with a valid `amount > 0`, `currency`, `interval`)
- **THEN** the system SHALL regenerate the product/price via `ensure_stripe_price`, create the checkout session, store the `signup_url`, and redirect back with a success message noting the price was regenerated

#### Scenario: Generate link blocked by inactive billing plan
- **WHEN** an administrator clicks "Generar link de suscripción" when the `BillingPlan` has `is_active_for_new_signups` set to `False`
- **THEN** the system SHALL display an error message and redirect back to the change form without creating a subscription

#### Scenario: Generate link hidden when a link exists
- **WHEN** an administrator opens an Artist change form and a `signup_url` exists (valid or expired)
- **THEN** the "Generar link de suscripción" action SHALL be hidden

#### Scenario: Generate link hidden and refused on the cash path
- **WHEN** an administrator opens an Artist change form whose subscription is a cash `pending`/`active` row, or executes the action URL directly for such an artist
- **THEN** the action SHALL be hidden, and direct execution SHALL be refused with 403 without mutation or email.

#### Scenario: Generate link regenerates a stale price and succeeds
- **WHEN** the stored `BillingPlan` product/price no longer exists in Stripe and the checkout raises a price/product `resource_missing` `InvalidRequestError`
- **THEN** the system SHALL regenerate the product/price via `ensure_stripe_price`, retry the checkout once with the fresh `price_xxx`, and on success store the `signup_url` and show a success message noting the price was regenerated

#### Scenario: Generate link fails loud on non-stale Stripe error
- **WHEN** `stripe.Customer.create` or `stripe.checkout.Session.create` raises `stripe.error.StripeError` that is not a stale-price/stale-customer signature (e.g. network, auth)
- **THEN** the system SHALL show `messages.error` with prefix `Stripe no respondió` (e.g. `f"Stripe no respondió: {e}"`), log `warning` with `artist_id`, and return `302` to the change form without creating a half-persisted `ArtistSubscription` link and without regenerating the product/price (message assertion shall check prefix, not exact ellipsis).

#### Scenario: Generate link recovers from a deleted customer
- **WHEN** the stored `stripe_customer_id` points to a customer deleted or missing in Stripe and `stripe.checkout.Session.create` raises the stale-customer error
- **THEN** the system SHALL clear the stale `stripe_customer_id`, create a fresh customer, retry the checkout session once, and store the new link — proceeding exactly as a successful generation.

### Requirement: Regenerate subscription link action
The system SHALL provide a "Regenerar link" changeform action on the Artist admin change page that reuses a valid existing checkout URL or creates a new one when expired. The action SHALL be visible whenever a subscription link exists (`signup_url` present, valid or expired) AND the row is `payment_method="online"` (never for cash rows). When the stored `BillingPlan.stripe_price_id` is empty (and email present with signups active), the system SHALL auto-create the product/price via `plan_sync.ensure_stripe_price` instead of refusing, and when the checkout raises a stale price/product error (a `resource_missing` `InvalidRequestError` referencing `price`/`product`/`price_xxx`/`prod_xxx`) the system SHALL regenerate via `ensure_stripe_price` and retry the checkout exactly once, showing a loud Spanish success message noting the price was regenerated. When Stripe raises any other `stripe.error.StripeError`, the system SHALL NOT return `500`; it SHALL `logger.warning`, show `messages.error` with prefix `Stripe no respondió`, and redirect `302` without persisting a partial URL. When the stored `stripe_customer_id` is missing or deleted in Stripe (a stale-customer `StripeError` on the checkout call), the system SHALL clear the stale `stripe_customer_id`, create a fresh customer, and retry the checkout session once before falling through to the generic error path.

#### Scenario: Regenerate link reuses valid URL
- **WHEN** an administrator clicks "Regenerar link" and the existing `signup_url` has not expired
- **THEN** the system SHALL reuse the existing URL without calling the Stripe checkout API and redirect back to the change form

#### Scenario: Regenerate link creates fresh session when expired
- **WHEN** an administrator clicks "Regenerar link" and the existing `signup_url` has expired
- **THEN** the system SHALL create a new checkout session, update the `signup_url` and `signup_url_expires_at`, and redirect back to the change form

#### Scenario: Regenerate link auto-creates price on empty price id
- **WHEN** an administrator clicks "Regenerar link" with an expired link and `BillingPlan.stripe_price_id` is empty (valid `amount > 0`, email present, signups active)
- **THEN** the system SHALL regenerate the product/price via `ensure_stripe_price`, create the checkout session, store the new `signup_url`, and redirect back with a Spanish success message noting the price was regenerated

#### Scenario: Regenerate link regenerates a stale price and succeeds
- **WHEN** the stored `BillingPlan` product/price no longer exists in Stripe and the checkout raises a price/product `resource_missing` `InvalidRequestError`
- **THEN** the system SHALL regenerate the product/price via `ensure_stripe_price`, retry the checkout once with the fresh `price_xxx`, and on success store the new `signup_url` and show a Spanish success message noting the price was regenerated

#### Scenario: Regenerate link hidden on the cash path
- **WHEN** an administrator opens an Artist change form whose subscription is a cash row
- **THEN** the "Regenerar link" action SHALL NOT be shown (cash rows never hold a `signup_url`).

#### Scenario: Stripe error during regeneration shows message not 500
- **WHEN** `stripe.Customer.create` or `stripe.checkout.Session.create` raises a non-stale `stripe.error.StripeError` during regeneration
- **THEN** the system SHALL show `messages.error` with prefix `Stripe no respondió` and return `302` without persisting a partial URL and without regenerating the product/price.

#### Scenario: Regenerate link recovers from a deleted customer
- **WHEN** the stored `stripe_customer_id` points to a customer deleted or missing in Stripe and the checkout call raises the stale-customer error
- **THEN** the system SHALL clear the stale `stripe_customer_id`, create a fresh customer, retry the checkout session once, and store the new link.
