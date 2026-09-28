## Context

`BillingPlan` is a `django-solo` singleton holding editable `amount/currency/interval` plus auto-managed `stripe_product_id/stripe_price_id`. `plan_sync.ensure_stripe_price(plan)` resolves/creates Product, creates Price, repoints default, archives old price (skipping ghosts), writes `BillingPlanPriceHistory`, stores new ids.

`generate_link` (`artworks/admin.py:672-769`) already self-heals two classes: stale customer (shared helper `_create_session_recovering_stale_customer`) and stale/empty price (inline heal calling `ensure_stripe_price` + one retry, loud message). `regenerate_link` (`:771-817`) only heals stale customer; on `No such price` (`resource_missing` + price signal, which `_is_stale_price_error` matches) it falls to generic `Stripe no respondió`. Prod confirmed: `Regenerar` + `sk_test` key + dead `price_1UB…` = dead end. Explore decisions: heal-blindly (no key-mode guard), mirror Generar's price-only bypass, Spanish zero-amount hint, lazy per-artist only.

## Goals / Non-Goals

**Goals:**
- `Regenerar link` auto-creates product/price on empty `stripe_price_id` and regenerates + retries once on stale price/product, identical to `Generar`.
- Single shared helper so both actions share trigger predicate, retry budget, logging, and messages.
- `generate_link` behavior unchanged (pure refactor onto helper).
- Spanish-only operator texts; audit via existing `BillingPlanPriceHistory`.

**Non-Goals:**
- No key-mode (test/live) guard; heal writes into whichever account the key points at.
- No changes to `open_portal`, `sync_from_stripe` (no `price_id` involved).
- No bulk reconcile command; no migration of old `cus_xxx`/`sub_xxx` rows.
- No rollback of orphan prices (log + History row, manual Dashboard cleanup, as today).

## Decisions

### D1. Shared `_checkout_with_price_heal(sub, artist, plan) -> (session, healed)`
Extract empty-price auto-create + checkout + stale-price regen + single retry into one helper returning the session and whether a heal fired. Both actions call it; stale-customer recovery stays nested inside via `_create_session_recovering_stale_customer`. Rationale: eliminates the Generar/Regenerar drift that caused this bug; one predicate, one retry budget. *Alternative:* duplicate the heal block in `regenerate_link` — rejected, drift-prone.

### D2. Price-only `_billing_blocked` bypass mirrored in Regenerar
When the sole blocker is empty `stripe_price_id` (email present, `is_active_for_new_signups=True`), proceed to auto-create instead of refusing. Other blockers still refuse. Rationale: parity with Generar's `:683-694` logic; an expired-link artist on a fresh DB is otherwise unrecoverable.

### D3. Reuse narrow `_is_stale_price_error`, single retry, fail-loud
Only `InvalidRequestError(code=resource_missing)` referencing price/product/stored ids triggers regen; auth/network/rate-limit never create products. At most one `ensure_stripe_price` + one checkout retry per request; further failure → `Stripe no respondió` + `302` + warning log with old/new ids. Rationale: wrong-account and orphan-spam safety already proven for Generar.

### D4. Spanish zero-amount hint
When auto-create fails because `amount <= 0` (fresh-DB default `0` bypasses `BillingPlanForm` validation), append a Spanish hint (e.g. `Configura el monto en Plan de suscripción.`) alongside `Stripe no respondió: …`. All admin-visible strings Spanish. Rationale: raw Stripe `Price.create` rejection is cryptic for operators.

### D5. `plan` freshness via in-place mutation
`ensure_stripe_price` mutates the passed `plan` in place, so the retry reads `plan.stripe_price_id` fresh without refetch. Helper relies on that; no extra `refresh_from_db` needed (same as Generar today).

## Risks / Trade-offs

- [Heal into wrong account] → Accepted per explore (heal-blindly); key hygiene remains operator duty.
- [Orphan price on retry failure] → Single retry only; History row + warning log; manual cleanup (unchanged semantics).
- [Concurrent double-heal] → `ensure_stripe_price` idempotence re-read covers sequential; tight race may double-create (extra History row, harmless) — accepted.
- [`expire_or_reuse` fast-path] → Returns existing URL without Stripe calls; an already-created session embeds its price, so no heal needed there.
- [Retry budget stacking] → Customer recovery (≤2 session calls) × price retry (≤2 rounds) = ≤4 session creates worst case; bounded, no loop.

## Migration Plan

1. Merge; `venv/bin/python manage.py test subscriptions --verbosity=2` (new Regenerar heal tests + existing suites).
2. Deploy additive; no migration/env change. Rollback = revert commit (Regenerar returns to fail-loud).
3. Prod unblock (no deploy needed today): click **Generar** once or save Plan admin to run `ensure_stripe_price`; verify new `price_xxx` resolves under the prod key.
