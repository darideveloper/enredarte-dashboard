## 1. Rework the cash-conversion guard

- [x] 1.1 Rename/rework `_is_online_started` (`artworks/admin.py:479` as `_has_active_stripe_billing`) to block only when `payment_method == "online"` AND (`status == PAST_DUE` OR (`status == ACTIVE` AND NOT `cancel_at_period_end`)); allow conversion for `pending`/`canceled`/`canceling`/`active`-with-cancel-requested
- [x] 1.2 Update the two call sites (`has_marcar_efectivo_permission` `:487`, `marcar_efectivo` `:729`) to the renamed predicate

## 2. Clear Stripe identifiers on cash conversion

- [x] 2.1 In `marcar_efectivo`, set `stripe_customer_id = ""` and `stripe_subscription_id = ""` and add both to the `update_fields` list (`artworks/admin.py:745,752-763`)

## 3. Recover from a deleted/broken Stripe customer

- [x] 3.1 Add `_is_stale_customer_error(e, customer_id)` predicate (`artworks/admin.py`) that recognizes a customer-missing/deleted `InvalidRequestError` (via `code == "resource_missing"` and/or the customer id appearing in the error text/`param`)
- [x] 3.2 Update `generate_link` to clear the stale `stripe_customer_id`, create a fresh customer, and retry the checkout session once before falling through to the generic `Stripe no respondió` path
- [x] 3.3 Update `regenerate_link` with the same stale-customer recovery (clear, recreate, retry once)
- [x] 3.4 Update `open_portal` to clear the stale `stripe_customer_id` and show `"El customer fue eliminado de Stripe; regenera el link"` on a stale-customer error
- [x] 3.5 Update `sync_from_stripe` to clear the stale `stripe_customer_id` and show `"El customer fue eliminado de Stripe; regenera el link"` on a stale-customer error

## 4. Update and add tests

- [x] 4.1 Update button-visibility tests (`subscriptions/tests.py`) to the new blocking rule (online `pending`/`canceling`/`active`-with-cancel allow `marcar_efectivo`; `active`-not-cancelling and `past_due` block)
- [x] 4.2 Add test: `marcar_efectivo` succeeds on an online `pending` row with a live link and clears `stripe_customer_id`/`stripe_subscription_id`
- [x] 4.3 Add test: `marcar_efectivo` allowed for `active`-with-`cancel_at_period_end=True` and for `canceling`
- [x] 4.4 Add test: `marcar_efectivo` still refused (403, no mutation/email) for `active`-not-cancelling and `past_due` online rows
- [x] 4.5 Add test: `generate_link` recovers when the stored customer is missing/deleted (new customer + retried session)
- [x] 4.6 Add test: `regenerate_link` recovers when the stored customer is missing/deleted (new customer + retried session)
- [x] 4.7 Add test: `open_portal` clears the stale id and shows the targeted warning on a missing customer
- [x] 4.8 Add test: `sync_from_stripe` clears the stale id and shows the targeted warning on a missing customer

## 5. Verify

- [x] 5.1 Run `venv/bin/python manage.py test subscriptions` (and `artworks` if touched) and confirm all tests pass