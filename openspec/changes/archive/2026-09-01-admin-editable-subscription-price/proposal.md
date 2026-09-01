## Why

Today, the only way to change the artist-subscription price is to log into the Stripe Dashboard, copy the new `price_xxx` id, paste it into the `BillingPlan` singleton (`stripe_price_id` field), and redeploy if the value isn't already in `STRIPE_PRICE_ID`. There is no amount, currency, or interval field — the admin form just takes a Stripe id string. Operators have no way to verify the price without leaving the dashboard, and changing the price requires out-of-band dashboard work plus a deploy/secret rotation.

This change makes the price **fully editable from the admin**: amount, currency (MXN/USD), and interval are entered as ordinary form fields; the app takes care of calling Stripe to create a new immutable `price_xxx` and updates the stored id automatically. Existing subscribers keep paying the old price (Stripe standard behavior), new sign-ups use the new price. The `STRIPE_PRICE_ID` env var is kept as a documented first-time seed.

## What Changes

- **Replace `BillingPlan.stripe_price_id` (manual copy-paste) with friendly form fields** `amount` (Decimal, > 0), `currency` (dropdown, `MXN` / `USD`), and `interval` (single choice, `month`).
- **Auto-manage the Stripe product/price ids behind the scenes**: the operator never types a `price_xxx`. On save, the app (a) ensures a Stripe product exists for the plan, (b) creates a new Stripe Price when amount/currency/interval change (Stripe Prices are immutable), (c) repoints the Stripe product's `default_price` to the new `price_xxx` (`Product.modify`) before archiving (Stripe blocks archiving the default price), then archives the old price (`active=False`) so it can't be reused, and (d) writes an audit row to a new `BillingPlanPriceHistory` model.
- **Fail loudly if Stripe is unreachable** during save — nothing is written to the DB, the operator sees an error.
- **Add a read-only "Confirmado por Stripe" line** on the change form that re-fetches `stripe.Price.retrieve(stripe_price_id)` on GET and shows the live amount/currency/interval, so the operator can verify the DB matches Stripe before editing.
- **Keep `STRIPE_PRICE_ID` env var as a documented first-time seed only** — the data migration uses it once, after that the admin form is the source of truth. No new env vars, no removed env vars.
- **Reuse the same Stripe product** across price changes; never create a new product — its `default_price` is kept in sync with the current `BillingPlan.stripe_price_id`.
- **Keep the django-solo singleton** — multiple plans / tiers remain out of scope (already explicit in `billing-plan/spec.md`).
- **Existing subscribers keep their old price** — Stripe's standard behavior: archiving the old `price_xxx` and creating a new one only affects new sign-ups. Artists already on a paid subscription continue to be billed the old amount on the old Stripe Subscription. This is documented in `docs/stripe-subscriptions.md` as a primary callout (no surprise, expected Stripe behavior).

## Capabilities

### New Capabilities

- `admin-editable-price`: end-to-end behavior for editing the subscription price from the Django admin — friendly form fields, automatic Stripe product/price creation, old-price archival, price-change history, live Stripe confirmation, and DB integrity guarantees when Stripe is unreachable.

### Modified Capabilities

- `billing-plan`: replace the manual `stripe_price_id` field with `amount` / `currency` / `interval`, add auto-managed `stripe_product_id` / `stripe_price_id` / `last_synced_stripe_at`, add the `BillingPlanPriceHistory` model, and require admin-side Stripe calls on price change.

## Impact

- **Code**:
  - `subscriptions/models.py` — `BillingPlan` field changes + new `BillingPlanPriceHistory` model.
  - `subscriptions/services/stripe_client.py` — add `get_or_create_product`, `create_price`, `archive_price`, `retrieve_price`, `set_product_default_price` (`Product.modify` for `default_price`).
  - `subscriptions/services/plan_sync.py` (new) — `ensure_stripe_price(plan, user)` orchestrator; idempotent, called from admin save.
  - `subscriptions/admin.py` — new `BillingPlanForm`, `save_model` calls `plan_sync`, inline history, read-only live-confirmation line.
  - `artworks/admin.py` — `_billing_blocked` simplified (only requires the auto-managed `stripe_price_id`).
  - `subscriptions/migrations/0004_admin_editable_price.py` — additive: add the new fields, remove the old `default=` from `stripe_price_id` (the field stays and is repurposed as auto-managed; its name is preserved so existing `plan.stripe_price_id` references continue to work), backfill from `STRIPE_PRICE_ID` best-effort, create `BillingPlanPriceHistory`.
- **Config**:
  - `.env.dev.example`, `.env.prod.example` — reword comment on `STRIPE_PRICE_ID` to "first-time seed only".
  - `project/settings.py` — unchanged.
- **Docs**:
  - `docs/stripe-subscriptions.md` — new "Editar el precio desde el admin" section + a "What happens to existing subscribers" callout.
- **Tests**:
  - `subscriptions/tests.py` — new `FormTest`, `EnsureStripePriceTest`, `LivePreviewTest`; refresh `BillingBlockedTest` for the new field set.
- **APIs / webhooks** — unchanged. Webhook handlers and the public checkout/cancel/portal-return landing pages are untouched. The link-generation endpoints continue to read `plan.stripe_price_id`; the only change is *where that id comes from*.
- **Stripe data** — additive: existing `price_1U8pogA37WTwarsM5km3SsV2` (test) / `price_1U98fBPSaJ0P1XliwCiPAwda` (live) and `prod_V984cG7B3YRfqq` are preserved. New prices are added under the same product on every change. Archived prices are flipped to `active=False`.
- **Backwards compatibility** — all existing data is preserved by the migration. Subscriptions created before this change keep using the original `price_xxx` (Stripe never re-bills an existing subscription against a new price). No public API or webhook contract changes.
