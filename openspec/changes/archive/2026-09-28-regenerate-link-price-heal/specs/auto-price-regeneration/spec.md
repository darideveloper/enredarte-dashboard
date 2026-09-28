## MODIFIED Requirements

### Requirement: Regenerate product/price on stale price during link generation
The system SHALL detect, during `Generar link de suscripción` and `Regenerar link`, when the stored `BillingPlan.stripe_price_id` / `stripe_product_id` no longer resolves in Stripe (a `stripe.error.InvalidRequestError` with `code == "resource_missing"` whose `param`/message references `price`, `product`, or the stored `price_xxx` / `prod_xxx`), and SHALL regenerate the product and price via `plan_sync.ensure_stripe_price`, then retry the checkout session **exactly once** using the fresh `stripe_price_id`. The regeneration SHALL re-read the persisted `BillingPlan` row before creating (idempotence check) and SHALL write a `BillingPlanPriceHistory` row via the existing flow.

#### Scenario: Checkout fails with stale price after account switch
- **WHEN** `Generar link` or `Regenerar link` (expired link) is invoked and `stripe.checkout.Session.create` raises `InvalidRequestError` `code == "resource_missing"` referencing the stored `price_xxx` / `prod_xxx`
- **THEN** the system SHALL call `ensure_stripe_price` once to create a fresh product+price in Stripe, retry the checkout with the new `stripe_price_id`, and on success persist the `signup_url` and show a loud success message that makes explicit the price was regenerated

#### Scenario: Only a single retry is attempted
- **WHEN** link-generation regeneration succeeds but the single retried checkout session also fails
- **THEN** the system SHALL show `messages.error` with prefix `Stripe no respondió`, log `warning` including the fresh `new_price_id` and old id, and return `302` without a third attempt and without rollback of the created price

### Requirement: Do not regenerate on non-staleness errors
The system SHALL NOT regenerate the product/price for any `StripeError` that is not a price/product `resource_missing` staleness signature — including `AuthenticationError`, `PermissionError`, rate-limit, and network/API errors. For those the system SHALL keep the current fail-loud behavior (`messages.error` prefix `Stripe no respondió`, `302`, no Stripe writes), so a misconfigured key can never silently create product/price in the wrong account.

#### Scenario: Auth error during checkout does not regenerate
- **WHEN** link checkout raises `stripe.error.AuthenticationError` (or any non-stale `StripeError`) referencing no stored price/product
- **THEN** the system SHALL show `messages.error` prefix `Stripe no respondió`, log `warning`, and return `302` with zero product/price creation and no retry

### Requirement: Auto-create product/price when price id is empty
The system SHALL, when `BillingPlan.stripe_price_id` is empty (fresh database / never configured), have `Generar link de suscripción` and `Regenerar link` first call `plan_sync.ensure_stripe_price` to create the product/price from the row's `amount` / `currency` / `interval` and then proceed to create the checkout session, instead of refusing with "Configura el precio". The system SHALL, when `amount <= 0` causes Stripe to reject the price creation, fail loud with the Stripe message plus a Spanish hint to configure the monto, and `302`.

#### Scenario: Link generation auto-creates on a fresh database
- **WHEN** `Generar link` or `Regenerar link` is invoked and `BillingPlan.stripe_price_id == ""` with a valid `amount > 0`, `currency`, and `interval`
- **THEN** the system SHALL regenerate via `ensure_stripe_price`, create the checkout with the new `stripe_price_id`, persist the `signup_url`, and show a loud success message noting the price was regenerated

#### Scenario: Zero amount fails with Spanish hint
- **WHEN** auto-create runs with `amount <= 0` and Stripe rejects the price creation
- **THEN** the system SHALL show `messages.error` with prefix `Stripe no respondió` plus a Spanish hint to configure the monto in Plan de suscripción, log `warning`, and return `302`

### Requirement: Force-create product when stored product is missing
The system SHALL, when regeneration runs and the stored `BillingPlan.stripe_product_id` no longer resolves in Stripe (it points to the old account or was deleted), create a fresh product rather than re-raising the `resource_missing` error, SHALL skip archiving the ghost old price, and SHALL store the new pair of product/price ids on the `BillingPlan` row.

#### Scenario: Stored product id is stale and must be recreated
- **WHEN** regeneration is triggered and `stripe.Product.retrieve(stripe_product_id)` raises `resource_missing`
- **THEN** the system SHALL call `stripe.Product.create(name=BillingPlan.name)`, create a new price under it, and persist the new `stripe_product_id` / `stripe_price_id` on the row with no price-archive call

### Requirement: Loud audited heal on link generation
Whenever regeneration fires during `Generar link` or `Regenerar link`, the system SHALL return an operator-facing success message that is distinct from the plain success message and indicates the price was regenerated (e.g. "Link generado. El precio fue regenerado automáticamente en Stripe." / "Link regenerado. El precio fue regenerado automáticamente en Stripe."), and SHALL record a `BillingPlanPriceHistory` row reflecting the new price for audit.

#### Scenario: Operator sees regenerated-price success
- **WHEN** link generation heals a stale or empty price and the checkout succeeds
- **THEN** the success message SHALL mention regeneration and a `BillingPlanPriceHistory` row SHALL exist reflecting the new `price_xxx`
