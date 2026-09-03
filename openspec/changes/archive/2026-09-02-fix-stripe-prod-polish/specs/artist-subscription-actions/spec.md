## MODIFIED Requirements

### Requirement: Generate subscription link action
The system SHALL provide a "Generar link de suscripción" changeform action on the Artist admin change page that creates a Stripe customer and checkout session when no subscription link has been generated yet. The action SHALL be visible only when the artist has no `signup_url` at all (no subscription or empty `signup_url`). When the Stripe API raises `stripe.error.StripeError` (network, auth, rate-limit), the system SHALL NOT return `500`; it SHALL `logger.warning` with the `artist_id` and error, show `messages.error` with prefix `Stripe no respondió` (e.g. `f"Stripe no respondió: {e}"`), and redirect `302` to the change form without persisting a partial link.

#### Scenario: Generate link for artist without a link
- **WHEN** an administrator opens an Artist change form and no subscription link exists (no subscription or empty `signup_url`)
- **THEN** the "Generar link de suscripción" action SHALL be shown and, when clicked, SHALL create a Stripe customer (if needed), create a checkout session, store the `signup_url` and `signup_url_expires_at`, set `status` to `PENDING`, and redirect back to the change form

#### Scenario: Generate link blocked by missing email
- **WHEN** an administrator clicks "Generar link de suscripción" for an artist with no email address
- **THEN** the system SHALL display an error message and redirect back to the change form without creating a subscription

#### Scenario: Generate link blocked by inactive billing plan
- **WHEN** an administrator clicks "Generar link de suscripción" when the `BillingPlan` has `is_active_for_new_signups` set to `False` or no `stripe_price_id`
- **THEN** the system SHALL display an error message and redirect back to the change form without creating a subscription

#### Scenario: Generate link hidden when a link exists
- **WHEN** an administrator opens an Artist change form and a `signup_url` exists (valid or expired)
- **THEN** the "Generar link de suscripción" action SHALL be hidden

#### Scenario: Stripe error during link generation shows message not 500
- **WHEN** `stripe.Customer.create` or `stripe.checkout.Session.create` raises `stripe.error.StripeError`
- **THEN** the system SHALL show `messages.error` with prefix `Stripe no respondió` (e.g. `f"Stripe no respondió: {e}"`), log `warning` with `artist_id`, and return `302` to the change form without creating a half-persisted `ArtistSubscription` link (message assertion shall check prefix, not exact ellipsis).


### Requirement: Regenerate subscription link action
The system SHALL provide a "Regenerar link" changeform action on the Artist admin change page that reuses a valid existing checkout URL or creates a new one when expired. The action SHALL be visible whenever a subscription link exists (`signup_url` present, valid or expired). When Stripe raises `stripe.error.StripeError`, the system SHALL NOT return `500`; it SHALL `logger.warning`, show `messages.error` with prefix `Stripe no respondió`, and redirect `302`.

#### Scenario: Regenerate link reuses valid URL
- **WHEN** an administrator clicks "Regenerar link" and the existing `signup_url` has not expired
- **THEN** the system SHALL reuse the existing URL without calling the Stripe checkout API and redirect back to the change form

#### Scenario: Regenerate link creates fresh session when expired
- **WHEN** an administrator clicks "Regenerar link" and the existing `signup_url` has expired
- **THEN** the system SHALL create a new checkout session, update the `signup_url` and `signup_url_expires_at`, and redirect back to the change form

#### Scenario: Stripe error during regeneration shows message not 500
- **WHEN** `stripe.Customer.create` or `stripe.checkout.Session.create` raises `stripe.error.StripeError` during regeneration
- **THEN** the system SHALL show `messages.error` with prefix `Stripe no respondió` and return `302` without persisting a partial URL.


### Requirement: Open customer portal action
The system SHALL provide an "Abrir Customer Portal" changeform action on the Artist admin change page that creates a Stripe billing portal session. The action SHALL be visible whenever a subscription link exists (`signup_url` present). When Stripe raises `stripe.error.StripeError` (e.g., deleted `cus_xxx`, auth fail), the system SHALL NOT return `500`; it SHALL `logger.warning`, show `messages.error` with prefix `Stripe no respondió`, and redirect `302`.

#### Scenario: Open portal redirects to portal URL in new tab
- **WHEN** an administrator clicks "Abrir Customer Portal" for an artist with a subscription link and a `stripe_customer_id`
- **THEN** the system SHALL create a Stripe billing portal session and redirect the browser to the portal URL in a new browser tab, keeping the admin on the current change form

#### Scenario: Open portal blocked without customer
- **WHEN** an administrator clicks "Abrir Customer Portal" for an artist with a subscription link but no `stripe_customer_id`
- **THEN** the system SHALL display a warning message and redirect back to the change form

#### Scenario: Stripe error during portal creation shows message not 500
- **WHEN** `stripe.billing_portal.Session.create` raises `stripe.error.StripeError`
- **THEN** the system SHALL show `messages.error` with prefix `Stripe no respondió` and return `302`.


### Requirement: Sync from Stripe action
The system SHALL provide a "Sincronizar desde Stripe" changeform action on the Artist admin change page that re-fetches the customer and subscription state from the Stripe API and updates the local `ArtistSubscription` and `Artist.is_active` accordingly. The action SHALL always be visible. The implementation MUST handle the Stripe SDK `ListObject` shape (`Subscription.list` returns `ListObject` with `.data`, not a plain `list`) via `subs.data if hasattr(subs,"data") else subs`, and MUST handle Stripe v15 `StripeObject` without `dict.get` via `sget`/`to_plain_dict`. Stripe API failures SHALL NOT return `500`; they SHALL `logger.warning`, show `messages.error` with prefix `Stripe no respondió`, and return `302`. The action SHALL perform a single DB save for `customer_email`+subscription fields (set `customer_email` via `sget(customer,"email")` before calling `apply_stripe_payload`, removing the double-save at `artworks/admin.py:513-514`), SHALL unwrap an expanded `customer` object (`{"id":...}`) to `cus_xxx` if present, and SHALL persist `customer_email` via `sget`.

#### Scenario: Sync updates subscription state
- **WHEN** an administrator clicks "Sincronizar desde Stripe" for an artist with a `stripe_customer_id` whose `Subscription.list` returns a `ListObject` with one active subscription (including a `StripeObject` whose `.get` is blocked and whose `unit_amount_decimal` is `Decimal`)
- **THEN** the system SHALL fetch the customer via `sget(customer,"email")` (or keep existing if `None`), unwrap the subscription via `ListObject.data[0]`, `apply_stripe_payload` via `sget`/`to_plain_dict(for_json=True)` handling `Decimal`, recompute `Artist.is_active` via `compute_is_active`, and redirect `302` with success message `Suscripción sincronizada: {prev} → {new}` (no `KeyError` at `stripe/_list_object.py:99`, no `AttributeError` at `stripe/_stripe_object.py:163`, no `TypeError: Decimal is not JSON serializable`).

#### Scenario: Sync without customer shows warning
- **WHEN** an administrator clicks "Sincronizar desde Stripe" for an artist without a `stripe_customer_id`
- **THEN** the system SHALL display a warning message and redirect back to the change form

#### Scenario: Sync shows error on Stripe failure not 500
- **WHEN** `stripe.Customer.retrieve` or `stripe.Subscription.list` raises `stripe.error.StripeError` (deleted `cus_xxx`, network, rate-limit)
- **THEN** the system SHALL show `messages.error` with prefix `Stripe no respondió`, log `warning` with `artist_id`, and return `302` without mutating `ArtistSubscription`/`Artist.is_active`.

#### Scenario: Sync handles expanded customer object

- **WHEN** Stripe returns the subscription's `customer` field as an expanded object `{"id":"cus_123", ...}` instead of string `cus_123`
- **THEN** `sget(stripe_sub,"customer")` SHALL be unwrapped: if the value is a dict-like with `id`, store `sget(value,"id")` as `stripe_customer_id`, not the dict string.

