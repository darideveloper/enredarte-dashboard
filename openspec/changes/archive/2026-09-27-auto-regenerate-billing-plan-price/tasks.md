## 1. Force-create product support

- [x] 1.1 In `subscriptions/services/plan_sync.py`, add a `force` path to `ensure_stripe_price`: when `stripe_client.get_or_create_product` reports the stored `stripe_product_id` as missing in Stripe (`resource_missing`), recreate a fresh product and skip archiving the ghost old price, instead of re-raising.
- [x] 1.2 In `subscriptions/services/stripe_client.py`, extend `get_or_create_product` to expose "create if stored id is missing" behavior (catch `resource_missing` on `Product.retrieve(existing_id)` and fall back to `Product.create`) so `ensure_stripe_price` can heal a stale product.
- [x] 1.3 Verify `ensure_stripe_price` still preserves the idempotence check (re-reads the persisted `(stripe_price_id, amount, currency, interval)` before creating) so a concurrent heal is a no-op.

## 2. Staleness predicate

- [x] 2.1 Add `_is_stale_price_error(e, plan)` in `artworks/admin.py` (mirroring `_is_stale_customer_error`): return `True` only for an `InvalidRequestError` with `code == "resource_missing"` whose `param`/message references `price`, `product`, or the stored `price_xxx` / `prod_xxx`; else `False`.
- [x] 2.2 Add unit tests for `_is_stale_price_error` covering the accepted cases (price/product `resource_missing`, stored id in message) and rejected cases (auth, network, rate-limit, non-`resource_missing`).

## 3. Auto-regenerate on Generar link

- [x] 3.1 In `artworks/admin.py:generate_link`, when `_billing_blocked` reports only a missing `stripe_price_id` (empty price, valid amount/currency/interval), call `plan_sync.ensure_stripe_price(plan)` to auto-create the product/price, then proceed to checkout (instead of refusing with "Configura el precio").
- [x] 3.2 In `artworks/admin.py:generate_link`, catch the stale-price failure around the checkout call: if `_is_stale_price_error(e, plan)`, call `plan_sync.ensure_stripe_price(plan)` once, re-fetch the updated `plan`, and retry the checkout session exactly once with the fresh `stripe_price_id`; otherwise fall through to the generic `StripeError` error path.
- [x] 3.3 Ensure any other `StripeError` (auth/network/rate-limit) still shows `messages.error` prefix `Stripe no respondió`, logs `warning`, and returns `302` with no product/price creation (per spec "Do not regenerate on non-staleness errors").

## 4. Loud success + audit

- [x] 4.1 In `artworks/admin.py:generate_link`, track whether a heal (regen + retry, or empty-price auto-create) fired; if so, show a distinct success message noting the price was regenerated (e.g. "Link generado. El precio fue regenerado automáticamente en Stripe."); otherwise keep the existing success message.
- [x] 4.2 Confirm the heal path writes a `BillingPlanPriceHistory` row (via `ensure_stripe_price`) and updates `last_synced_stripe_at` + auto-managed ids as audit.

## 5. Tests

- [x] 5.1 Add `subscriptions/services/plan_sync` tests: force-create path when old product is `resource_missing` (fresh product created, no archive call), idempotent concurrent no-op, and empty-price first-creation.
- [x] 5.2 Add `artworks/admin` endpoint tests for `generate_link`: (a) auto-creates price on empty `stripe_price_id` with valid amount and succeeds; (b) regenerates on stale price `resource_missing` and retries once then succeeds with the "regenerado" message; (c) heal succeeds but retried checkout fails → `messages.error` prefix `Stripe no respondió`, no third attempt, orphan price id logged, `302`.
- [x] 5.3 Add a regression test that a non-stale `StripeError` (e.g. `AuthenticationError`) during `generate_link` does NOT call `ensure_stripe_price` and does NOT create a product/price.
- [x] 5.4 Add a `BillingPlanAdmin` save test proving the admin price-form heals a stale product after an account switch: patch `stripe.Product.retrieve` to raise `resource_missing` for the stored `prod_xxx`, save the form with a new `amount`, and assert a fresh product/price is created, `stripe_product_id`/`stripe_price_id` persist, and a `BillingPlanPriceHistory` row is written — so changing the price from the admin works without manual Stripe cleanup.
- [x] 5.5 Run full suite `venv/bin/python manage.py test --verbosity=2` (subscriptions + artworks) and confirm green with no `TypeError`/`AttributeError`/`KeyError` regressions.

## 6. Docs

- [x] 6.1 Update `docs/stripe-subscriptions.md` (Editing the price / link generation sections) and `docs/stripe-account-setup.md` to note the auto-regeneration behavior on account switch and empty price.