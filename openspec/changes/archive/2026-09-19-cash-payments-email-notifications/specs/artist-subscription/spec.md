## MODIFIED Requirements

### Requirement: ArtistSubscription model lifecycle
The system SHALL provide an `ArtistSubscription` model with a one-to-one relationship to `Artist` (via `artist.subscription`) so each artist has at most one current subscription record. The model MUST have `verbose_name`, all field-level `verbose_name`/`help_text`, and a content-based `__str__` returning `"{artist} — {status_display}"`. The model SHALL carry a `payment_method` field with choices `online` (default) and `cash`, distinguishing Stripe-tracked rows from manually-managed cash rows. All admin-visible strings of the field SHALL be Spanish: `verbose_name="Método de pago"`, `help_text="En línea: la suscripción se gestiona en Stripe. En efectivo: el control es manual desde el admin, sin Stripe."`, choice labels `"En línea"` and `"Efectivo"`. Cash rows SHALL reuse the existing `Status` values and `compute_is_active()` derivation; no new status values are introduced.

#### Scenario: Creating an ArtistSubscription for an Artist
- **WHEN** any code or operator triggers subscription creation for an `Artist` who has none
- **THEN** exactly one `ArtistSubscription` row SHALL be persisted with `status="pending"`, `payment_method="online"` (unless the cash flow explicitly sets `"cash"`), no Stripe identifiers, an empty `signup_url`, and `last_synced_at=now()`.

#### Scenario: Attempting a second subscription for the same artist
- **WHEN** any code attempts to save a second `ArtistSubscription` for an `Artist` that already has one
- **THEN** the database SHALL reject the write due to the unique one-to-one key.

#### Scenario: Payment method labels render in Spanish
- **WHEN** an administrator views the `ArtistSubscription` admin (list, form, or read-only inline)
- **THEN** the field SHALL display as "Método de pago" with choices "En línea" and "Efectivo".

### Requirement: Mirror of Stripe identifiers
The system SHALL store, for each online `ArtistSubscription`: `stripe_customer_id` (unique, nullable), `stripe_subscription_id` (unique, nullable), and a `raw_state` JSON snapshot of the last Stripe object processed for debugging. Cash rows (`payment_method="cash"`) SHALL keep both Stripe identifier fields empty and SHALL store a small audit dict (`{"cash": true, ...}`) in `raw_state` instead of a Stripe object.

#### Scenario: Customer id assigned at link generation
- **WHEN** an operator generates a subscription link for an artist
- **THEN** the `ArtistSubscription` row SHALL persist the `cus_xxx` returned by Stripe as `stripe_customer_id`.

#### Scenario: Subscription id assigned at first charge
- **WHEN** Stripe delivers a `customer.subscription.created` event after a successful first payment
- **THEN** the matching `ArtistSubscription` SHALL have `stripe_subscription_id` set to `sub_xxx` and `status="active"`.

#### Scenario: Cash transition stores no Stripe identifiers
- **WHEN** any cash admin action completes
- **THEN** `stripe_customer_id` and `stripe_subscription_id` SHALL remain empty and `raw_state` SHALL hold the cash audit dict.
