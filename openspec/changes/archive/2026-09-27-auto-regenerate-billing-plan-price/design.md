## Context

`BillingPlan` is a `django-solo` singleton (`subscriptions/models.py:39`) holding
editable `amount` / `currency` / `interval` plus read-only auto-managed
`stripe_product_id` / `stripe_price_id`. `plan_sync.ensure_stripe_price(plan)`
(`subscriptions/services/plan_sync.py:20`) is the existing orchestrator: it
resolves/creates a Product, creates a Price, repoints the default, archives the
old price, writes a `BillingPlanPriceHistory` row, and stores the new ids.

`generate_link` (`artworks/admin.py:615`) is the entry point. It already
self-heals one failure class — a deleted/dangling **customer** — via
`_create_session_recovering_stale_customer` + `_is_stale_customer_error`
(`artworks/admin.py:592,571`). The **price/product** can go stale the same way:
after a Stripe account switch the stored `price_xxx` / `prod_xxx` no longer exist
under the current key, so checkout raises a `resource_missing` `InvalidRequestError`
and the user gets a dead end with no in-product recovery.

Today `stripe_price_id == ""` is handled by `_billing_blocked` refusing with
"Configura el precio". There is no delete/recreate admin UI; recovery is manual.

This change adds the same self-healing the customer already enjoys, but for the
shared plan price/product, scoped to `Generar link` only.

## Goals / Non-Goals

**Goals:**
- `Generar link` recovers automatically when the stored product/price is
  missing in Stripe (account switch, deleted/archived price) by regenerating and
  retrying once.
- `Generar link` auto-creates product/price when `stripe_price_id` is empty.
- Narrow trigger so only real staleness triggers regeneration (no wrong-account
  writes, no orphan-price spam on transient errors).
- Loud operator feedback when a heal fires; audit trail via existing
  `BillingPlanPriceHistory`.

**Non-Goals:**
- No changes to `Regenerar link`, `Sincronizar desde Stripe`, or `Customer Portal`.
- No migration of existing old-account `ArtistSubscription` rows (confirmed:
  lazy per-artist recovery via the existing stale-customer handling is kept;
  no bulk reconcile command in this change).
- No public API changes, no new dependencies, no DB schema changes.
- No rollback / auto-archive of orphan prices on retry failure (logged instead).

## Decisions

### D1. Regeneration entry point: hook into `generate_link`, reuse `ensure_stripe_price`
The heal lives in the `generate_link` flow (and the shared stale-customer
checkout helper), calling the existing `ensure_stripe_price`. Rationale: the
plan-sync orchestration + history write already exists and is tested; reusing it
avoids a second product/price-creation implementation.
*Alternative:* a dedicated standalone "regenerate plan" routine — rejected as
duplicative and risk of drift.

### D2. Force-create path in `ensure_stripe_price` / `get_or_create_product`
The current `get_or_create_product(name, existing_id)` does `Product.retrieve(existing_id)`,
which re-raises `resource_missing` after an account switch — the exact error the
heal is trying to fix. Add a force-create path: when the stored `stripe_product_id`
is missing in Stripe, create a fresh Product, mint a new Price, and **skip
archiving** the ghost old price. Because `BillingPlanAdmin.save_model`
(`subscriptions/admin.py:151`) also routes through `ensure_stripe_price`, this
same force-create path transparently heals the admin price-form after an account
switch, so operators can keep editing the price from the admin without manual
Stripe cleanup (explicit in `admin-editable-price` delta spec).
*Alternative:* keep retrieve-fail semantics; accept that the heal can't recover
product staleness — rejected; that is precisely the reported bug.

### D3. Narrow trigger predicate `_is_stale_price_error(e, plan)`
Analogous to `_is_stale_customer_error`. Regenerate only when the failure is an
`InvalidRequestError` (code `resource_missing`) whose message/`param` references
a `price` / `product`, or contains the stored `price_xxx` / `prod_xxx`. All other
`StripeError` (auth, permissions, network, rate-limit, 5xx) **never** regenerate.
*Why:* the account-switch / deleted-price case surfaces as `resource_missing`
on price/product; a broad "any InvalidRequestError or any error" trigger would
silently create products in the wrong account and mint orphan prices on transient
failures (the `plan_sync` docstring already warns "retry creates another price").
Companion refinement: `_is_stale_customer_error` now requires a customer signal
(`customer` / `cus_` in the message/`param`, or the stored id) before treating a
`resource_missing` as a stale customer, so a price error is never misclassified
as a customer error (which would otherwise orphan a fresh customer per price-heal).

### D4. Single retry, then fail loud
Regeneration runs at most once per `Generar link` request; if the retried
checkout still fails, fall through to the existing generic "Stripe no respondió"
error + `302`, logging both the fresh `new_price_id` and the old id. No rollback
(the price was created; operator does Dashboard cleanup, matching today's
documented orphan behavior).

### D5. Wrong-account guard
Regeneration only fires on the narrow price/product-missing signature (D3), which
is what an account switch produces. A key that points at the wrong account but
where the price *resolves* is outside this change's scope (fail-loud path is
already what `resource_missing` avoids). If a test/live key guard is desired, it
is captured as an Open Question rather than a decision, to keep scope minimal.

### D6. Empty-price auto-create
When `_billing_blocked` finds `stripe_price_id == ""`, `generate_link` calls
`ensure_stripe_price(plan)` first (creating product+price from the row) and
proceeds instead of refusing. `amount` must be > 0 (form-validated; if it's 0,
`Price.create` will fail and bubble to fail-loud).
*Alternative:* keep refusing and require manual config — rejected per user
decision ("Auto-create").

### D7. Loud success
When a heal fires and the retried checkout succeeds, return a distinct success
message (e.g. "Link generado. El precio fue regenerado automáticamente en
Stripe.") instead of the plain success, so the operator knows an account/price
recovery happened. The `BillingPlanPriceHistory` row is the persistent audit.

## Risks / Trade-offs

- [Wrong key after account switch resolved price] → Out of scope for the trigger;
  guarded by the narrow predicate so this can't auto-create into an account we
  only read from.
- [Orphan `price_xxx` spam from repeated clicks] → Regeneration retries once per
  request only, and only on the narrow signature; each regeneration writes a
  History row for traceability.
- [Heal fires but retry still fails] → Fail loud, log both price ids, no
  rollback; prices are archived conservatively (operator cleanup), consistent
  with existing "retry creates another price" behavior.
- [Concurrent operators both see stale price] → `ensure_stripe_price` re-reads the
  persisted row before creating (idempotence check), so a second caller after the
  first finishes is a no-op; a tight simultaneous double-create remains possible
  and is acceptable (extra History row, harmless product/price).
- [`amount == 0` fresh DB] → `Price.create` rejects it; heal fails loud with the
  Stripe message, operator fills the amount via the admin form (unchanged path).

## Migration Plan

1. Merge; run `manage.py test` (new heal tests + existing subscription suites).
2. Deploy as-is (additive behavior; no migration, no env change).
3. Rollback: revert the commit; `generate_link` returns to the previous
   fail-loud semantics. No data migration to reverse.

## Open Questions

- Should a test-vs-live key guard (e.g. `ENV=prod` + `sk_test_…`) refuse healing
  too? Current scope covers only the price/product-missing signature; a key-type
  guard would be a small addition if wanted.
- Reuse the heal across `regenerate_link`/`sync_from_stripe` later? Scoped out now.