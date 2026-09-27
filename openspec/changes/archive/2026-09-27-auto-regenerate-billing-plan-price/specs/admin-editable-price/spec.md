# admin-editable-price Delta Spec

## MODIFIED Requirements

### Requirement: Auto-managed Stripe product and price ids

The system SHALL keep `BillingPlan.stripe_product_id` and `BillingPlan.stripe_price_id` populated at all times so that link generation always has a valid Stripe price to pass to `create_checkout_session`. These fields MUST be read-only in the admin form; they are written exclusively by the save flow that talks to Stripe. In addition, `ensure_stripe_price` SHALL support a force-create path for the `auto-price-regeneration` capability: when the stored `stripe_product_id` no longer resolves in Stripe (deleted, or stale after an account switch), it SHALL create a fresh product instead of re-raising `resource_missing`, and SHALL skip archiving a ghost old price.

#### Scenario: First-time save creates a Stripe product

- **WHEN** the `BillingPlan` is saved for the first time and `stripe_product_id` is empty
- **THEN** the system SHALL call `stripe.Product.create(name=BillingPlan.name)`, store the returned product id on `BillingPlan.stripe_product_id`, and create a new `Price` for that product with the form's `amount`, `currency`, and `interval`.

#### Scenario: Subsequent saves reuse the existing product

- **WHEN** the `BillingPlan` is saved and `stripe_product_id` is already set and resolves in Stripe
- **THEN** the system SHALL NOT call `stripe.Product.create` and SHALL only call `stripe.Price.create`, `stripe.Product.modify` (to repoint `default_price` to the new price), and `stripe.Price.update` for the old price as needed.

#### Scenario: Regeneration force-creates a stale product

- **WHEN** the `auto-price-regeneration` flow calls `ensure_stripe_price` and the stored `stripe_product_id` raises `resource_missing` in Stripe (deleted / old account)
- **THEN** the system SHALL call `stripe.Product.create(name=BillingPlan.name)`, create a new price under it, persist the new `stripe_product_id` / `stripe_price_id`, and SHALL NOT archive the ghost old price.

#### Scenario: Admin price-form save heals a stale product after an account switch

- **WHEN** a staff member opens the "Plan de suscripción" admin after a Stripe account switch (stored `stripe_product_id` raises `resource_missing` in Stripe) and saves a price change
- **THEN** the admin save SHALL force-create a fresh product via `ensure_stripe_price`, create a new price, persist the new `stripe_product_id` / `stripe_price_id`, write a `BillingPlanPriceHistory` row, and show the "Confirmado por Stripe" preview resolving to the new price — the operator SHALL be able to change the price from the admin without manual Stripe cleanup.

### Requirement: Idempotent regeneration re-reads the persisted row

The `ensure_stripe_price` SHALL, before creating, re-read the persisted `BillingPlan` row and, if the persisted `(stripe_price_id, amount, currency, interval)` already matches (a concurrent/heal already completed), SHALL make no Stripe calls and reuse the stored `stripe_price_id`, so repeated or concurrent generation cannot mint an unbounded number of prices.

#### Scenario: Concurrent heal is a no-op for the second caller

- **WHEN** two `Generar link` requests observe a stale price and both call `ensure_stripe_price`,
  and the first completes (persisting the new `price_xxx`)
- **THEN** the second caller, re-reading the persisted row, SHALL see a matching `(stripe_price_id, amount, currency, interval)` and SHALL reuse it without creating another price or history row.

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