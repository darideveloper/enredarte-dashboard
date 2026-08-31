# billing-plan Specification

## Purpose
TBD - created by archiving change add-stripe-artist-subscriptions. Update Purpose after archive.
## Requirements
### Requirement: Singleton BillingPlan configuration
The system SHALL provide a `BillingPlan` model registered with `django-solo` so that exactly one configuration row exists and is editable as a singleton in the Django Unfold admin under a "Plan de suscripción" section.

#### Scenario: Editing the singleton BillingPlan
- **WHEN** an administrator opens the "Plan de suscripción" section in the admin
- **THEN** a single edit page SHALL render the `BillingPlan` fields (`name`, `stripe_price_id`, `currency`, `grace_period_days`, `is_active_for_new_signups`) and saving the form SHALL update the singleton row.

#### Scenario: Only one BillingPlan row exists
- **WHEN** any code accesses `BillingPlan.get_solo()`
- **THEN** exactly one row SHALL be returned and no code path SHALL be able to create additional rows.

### Requirement: BillingPlan fields
The system SHALL expose the following fields on `BillingPlan`, each with `verbose_name` and (where useful) `help_text`:
- `name` (CharField, default "Membresía Enredarte")
- `stripe_price_id` (CharField, `price_xxx` from Stripe; required for new sign-ups)
- `currency` (CharField, ISO 4217; default `MXN`)
- `grace_period_days` (PositiveIntegerField, default `3`)
- `is_active_for_new_signups` (BooleanField, default `True`)

#### Scenario: Default values on first access
- **WHEN** the singleton `BillingPlan` row is created the first time it is requested
- **THEN** the row SHALL be saved with `name="Membresía Enredarte"`, `currency="MXN"`, `grace_period_days=3`, `is_active_for_new_signups=True`, and an empty `stripe_price_id`.

### Requirement: Single stripe_price_id enforcement on link generation
The system SHALL refuse to generate a subscription link when `BillingPlan.is_active_for_new_signups` is `False` or when `BillingPlan.stripe_price_id` is empty, returning an operator-visible error.

#### Scenario: Attempting to generate a link while sign-ups are paused
- **WHEN** an operator triggers "Generar link de suscripción" while `BillingPlan.is_active_for_new_signups=False`
- **THEN** the system SHALL not call the Stripe API and SHALL show an admin error message ("Las nuevas suscripciones están pausadas en el Plan de suscripción.").

#### Scenario: Attempting to generate a link without a stripe_price_id
- **WHEN** an operator triggers "Generar link de suscripción" while `BillingPlan.stripe_price_id` is empty
- **THEN** the system SHALL not call the Stripe API and SHALL show an admin error message ("Configura el `stripe_price_id` en Plan de suscripción antes de generar links.").

### Requirement: BillingPlan translatable admin labels
The system SHALL provide Spanish and English `gettext` translations for the `BillingPlan` model name (`"Plan de suscripción"` / `"Subscription Plan"`) and each of its field labels.

#### Scenario: Spanish admin label
- **WHEN** an administrator with Spanish locale opens the "Plan de suscripción" singleton
- **THEN** every field label SHALL be rendered in Spanish (e.g. `"ID de precio en Stripe"`, `"Período de gracia (días)"`, `"Aceptar nuevas suscripciones"`).

#### Scenario: English admin label
- **WHEN** an administrator with English locale opens the "Subscription Plan" singleton
- **THEN** every field label SHALL be rendered in English (e.g. `"Stripe price ID"`, `"Grace period (days)"`, `"Accept new subscriptions"`).

### Requirement: Single canonical plan today
The system SHALL support exactly one active plan through `BillingPlan`; multiple tiers are out of scope today. The design MUST NOT add any multi-plan selector to admin views or onboarding flows.

#### Scenario: UI does not offer tier choice
- **WHEN** an operator opens the artist subscription controls
- **THEN** the system SHALL NOT present a "select plan" dropdown; the single `BillingPlan` SHALL be used unconditionally.

