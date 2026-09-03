## MODIFIED Requirements

### Requirement: Editable price form fields
The system SHALL expose the artist-subscription price in the `BillingPlan` admin as three ordinary form fields: `amount` (decimal, > 0), `currency` (dropdown restricted to `MXN` and `USD`), and `interval` (single choice `month`). The operator MUST NOT be required to type a Stripe `price_xxx` id anywhere in the form.

#### Scenario: Editing amount only
- **WHEN** a staff member opens the "Plan de suscripción" admin and changes only the `amount` field (e.g. from `299.00` to `349.00`)
- **THEN** the form SHALL save the new amount, the system SHALL create a new Stripe Price for the new amount under the same Stripe product, the new `price_xxx` SHALL be stored on `BillingPlan.stripe_price_id`, and the old `price_xxx` SHALL be archived (`active=False`).

#### Scenario: Switching currency from MXN to USD
- **WHEN** a staff member saves the form with `amount=15.00, currency=USD, interval=month`
- **THEN** the system SHALL create a new Stripe Price in USD on the same product, archive any previous MXN price, and store the new `price_xxx` on `BillingPlan.stripe_price_id`.

#### Scenario: Rejecting invalid values
- **WHEN** a staff member submits the form with `amount=0`, `amount=-1`, a missing amount, a currency outside `{MXN, USD}`, or any interval other than `month`
- **THEN** the form SHALL fail validation, the database SHALL NOT be modified, and the system SHALL NOT call the Stripe API.

### Requirement: Auto-managed Stripe product and price ids
The system SHALL keep `BillingPlan.stripe_product_id` and `BillingPlan.stripe_price_id` populated at all times so that link generation always has a valid Stripe price to pass to `create_checkout_session`. These fields MUST be read-only in the admin form; they are written exclusively by the save flow that talks to Stripe.

#### Scenario: First-time save creates a Stripe product
- **WHEN** the `BillingPlan` is saved for the first time and `stripe_product_id` is empty
- **THEN** the system SHALL call `stripe.Product.create(name=BillingPlan.name)`, store the returned product id on `BillingPlan.stripe_product_id`, and create a new `Price` for that product with the form's `amount`, `currency`, and `interval`.

#### Scenario: Subsequent saves reuse the existing product
- **WHEN** the `BillingPlan` is saved and `stripe_product_id` is already set
- **THEN** the system SHALL NOT call `stripe.Product.create` and SHALL only call `stripe.Price.create`, `stripe.Product.modify` (to repoint `default_price` to the new price), and `stripe.Price.update` for the old price as needed.

### Requirement: Stripe-down behavior on save
The system SHALL treat any failure to reach Stripe during a `BillingPlan` save as a hard error: no row in `BillingPlan` and no row in `BillingPlanPriceHistory` SHALL be persisted, and the operator SHALL see an admin error message identifying the Stripe error. The price creation failure SHALL be logged via `logger.exception`/`warning`.

#### Scenario: Network failure during save
- **WHEN** a staff member saves the form and the Stripe API call raises any `stripe.error.StripeError` (network, auth, API error, rate limit)
- **THEN** the form save SHALL abort, the database SHALL remain unchanged (no `BillingPlan` write, no `BillingPlanPriceHistory` write), and an admin error message SHALL be shown describing the Stripe error.

#### Scenario: Read-only preview does not block the form
- **WHEN** a staff member opens the change form and the read-only "Confirmado por Stripe" fetch fails (network, missing key, archived price)
- **THEN** the form SHALL still render and SHALL still be saveable; the preview line SHALL be absent or read "(no se pudo confirmar)" but the absence of the preview MUST NOT raise an exception to the operator, and a `logger.warning` SHALL record the `stripe_price_id` and error.

### Requirement: Old price archival on every change
The system SHALL repoint the product's `default_price` to the new price and set the previous `BillingPlan.stripe_price_id` to `active=False` in Stripe whenever a new price is created, and SHALL record the archival in the corresponding `BillingPlanPriceHistory` row. If `stripe.Price.modify(active=False)` raises after the new price has been created and `default_price` repointed, the system SHALL `logger.warning` with the orphan `new_price_id` and `old_price_id` (the new price remains in Stripe, DB stays old, next save will create another price — documented orphan).

#### Scenario: Archiving the old price
- **WHEN** the save flow creates a new Stripe Price (because amount, currency, or interval changed) and an old `stripe_price_id` is stored on the `BillingPlan`
- **THEN** the system SHALL call `stripe.Product.modify(product_id, default_price=new_price_id)` before `stripe.Price.update(old_stripe_price_id, active=False)` and SHALL persist a `BillingPlanPriceHistory` row with `old_price_archived=True`.

#### Scenario: No old price to archive
- **WHEN** the save flow creates a new Stripe Price and `BillingPlan.stripe_price_id` is empty (first save)
- **THEN** the system SHALL NOT call `stripe.Price.update` and the `BillingPlanPriceHistory` row SHALL have `old_stripe_price_id=""`.

#### Scenario: Idempotent save with no Stripe round-trip
- **WHEN** a staff member saves the form without changing `amount`, `currency`, or `interval` and `stripe_price_id` is already set
- **THEN** the system SHALL NOT call any Stripe API and SHALL NOT write a `BillingPlanPriceHistory` row.

### Requirement: Price change history audit
The system SHALL persist an append-only `BillingPlanPriceHistory` row for every successful price change, capturing the previous and new Stripe price ids, the form values that produced the change (`amount`, `currency`, `interval`), whether the old price was archived, when the change happened, and which staff user triggered it. The creation SHALL be `logger.info` with the `amount` and `new_price_id`.

#### Scenario: History row created on change
- **WHEN** a staff member saves the form and the save flow creates a new Stripe Price
- **THEN** a `BillingPlanPriceHistory` row SHALL be created with the old and new price ids, the new `amount`/`currency`/`interval`, `old_price_archived=True`, `changed_at=now()`, and `changed_by=request.user` (or `NULL` if no user, e.g. management command).

#### Scenario: History visible in the admin
- **WHEN** a staff member opens the `BillingPlan` change page
- **THEN** a read-only inline list of `BillingPlanPriceHistory` rows SHALL be rendered (most recent first) showing `changed_at`, `changed_by`, `old_stripe_price_id` → `new_stripe_price_id`, `amount` `currency` `/` `interval`, and whether the old price was archived.

### Requirement: Live "Confirmado por Stripe" preview
The system SHALL display a read-only confirmation line on the `BillingPlan` change form that re-fetches the current `stripe_price_id` from Stripe via `stripe_client.retrieve_price` and shows the live amount, currency, and interval using `sget(price,"unit_amount")`, `sget(price,"currency")`, `sget(price,"recurring")` then `sget(recurring,"interval") or ""` (uniform `sget`, no `isinstance(dict)` + `recurring.get` branch which is blocked for `StripeObject` in `stripe>=15`), plus `sget(price,"id")`. The preview SHALL be stored per-request via `request._stripe_live_summary` (thread-safe, not `self._stripe_live_summary` singleton race) and SHALL `logger.warning` on failure.

#### Scenario: Preview matches the stored price
- **WHEN** a staff member opens the change form and `stripe_price_id` is set and `stripe.Price.retrieve` returns a `StripeObject` with `recurring` as `StripeObject` (including `Decimal` payload)
- **THEN** the form SHALL render a read-only line "Confirmado por Stripe: <amount> <currency> / <interval> (<stripe_price_id>)" using `sget` (no `AttributeError: 'get' is a dict method`), and the line SHALL be stored on `request`, not on `self`, so concurrent admin requests do not see the wrong summary. On `StripeError` or `Decimal` payload, the preview SHALL degrade to `"(no se pudo confirmar)"` with a `warning` log, not `500`.

#### Scenario: Preview is not editable
- **WHEN** a staff member views the form
- **THEN** the preview line SHALL be rendered as plain text (not a form input) and SHALL NOT be posted back when the form is submitted.

### Requirement: First-time seed from STRIPE_PRICE_ID env var
The system SHALL treat the `STRIPE_PRICE_ID` environment variable as a first-time seed only: the data migration MAY use it to backfill `BillingPlan` (best-effort `stripe.Price.retrieve` to seed `amount`/`currency`/`interval`), and any subsequent read of the singleton SHALL use the `BillingPlan` row in the database, not the env var. Operators editing the price in the admin SHALL NEVER need to set or change `STRIPE_PRICE_ID`.

#### Scenario: Migration seeds from STRIPE_PRICE_ID when reachable
- **WHEN** the data migration runs and `STRIPE_PRICE_ID` is set, `stripe.api_key` is configured, and the API call to `stripe.Price.retrieve(STRIPE_PRICE_ID)` succeeds
- **THEN** the migration SHALL populate `BillingPlan.amount`, `BillingPlan.currency`, `BillingPlan.interval`, and the new auto-managed `stripe_price_id` / `stripe_product_id` from the retrieved Price object.

#### Scenario: Migration leaves amount=0 when Stripe is unreachable
- **WHEN** the data migration runs and either `STRIPE_PRICE_ID` is empty, the Stripe API key is missing, or `stripe.Price.retrieve` raises any exception
- **THEN** the migration SHALL leave `BillingPlan.amount=0` and SHALL NOT raise; the operator SHALL be able to complete the first-time configuration by saving the admin form (which will then create the price in Stripe).

#### Scenario: Env var is not consulted after migration
- **WHEN** any code reads the live `BillingPlan` singleton
- **THEN** the values SHALL come from the database row, not from `settings.STRIPE_PRICE_ID`; the env var MUST NOT be a runtime source of truth.

### Requirement: Link generation uses the auto-managed price id
The system SHALL continue to call `stripe_client.create_checkout_session(customer, metadata={"artist_id": ...}, price_id=BillingPlan.stripe_price_id)` from the `Generar link de suscripción` and `Regenerar link` admin actions. The only change is that the `price_id` argument is now the auto-managed field populated by the price-change flow, not a manually-typed value.

#### Scenario: First link after a price change
- **WHEN** a staff member triggers "Generar link de suscripción" for an artist after the `BillingPlan` amount has been edited and a new Stripe Price has been created
- **THEN** the new Checkout Session SHALL be created using the new `price_xxx`, the artist's `signup_url` SHALL be persisted, and the artist's `is_active` SHALL be set per `compute_is_active`.

#### Scenario: Old subscribers keep their old price
- **WHEN** an artist is already subscribed (their Stripe Subscription references an old archived `price_xxx`) and a staff member changes the `BillingPlan` amount
- **THEN** the artist's existing subscription SHALL continue to be billed at the old amount (Stripe's standard behavior for archived prices on existing subscriptions), and only NEW sign-ups SHALL use the new price.

