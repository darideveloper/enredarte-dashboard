## Why

Prod `Regenerar link` fails with `Stripe no respondió: No such price: 'price_1UB…'` while `Generar link` self-heals the same error. The price/product heal from `auto-regenerate-billing-plan-price` was scoped to `Generar` only, so every expired-link artist after a price delete/archive or Stripe account (or test/live mode) switch is a dead end with no in-product recovery.

## What Changes

- Extract a shared `_checkout_with_price_heal()` helper in `artworks/admin.py` (empty-price auto-create + stale price/product regen + exactly one checkout retry, preserving the inner stale-customer recovery).
- Wire both `generate_link` and `regenerate_link` to the helper; `regenerate_link` keeps its `expire_or_reuse_session` fast-path and gains the same heal + loud regenerated-price success message.
- `regenerate_link` mirrors `generate_link`'s price-only `_billing_blocked` bypass (still blocks on missing email / paused signups); zero-amount auto-create failure adds a Spanish operator hint.
- Heal-blindly: no test/live key-mode guard (per explore decision); per-artist lazy recovery only, no bulk reconcile.
- Specs + tests + `docs/stripe-subscriptions.md` updated to cover the Regenerar heal path.

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `auto-price-regeneration`: extend the heal contract from Generar-only to Generar + Regenerar (empty-price + stale-price triggers, single retry, loud message).
- `artist-subscription-actions`: `regenerate_link` gains empty-price auto-create and stale-price regen behavior instead of generic fail.

## Impact

- `artworks/admin.py` — new shared helper + `generate_link` refactor (no behavior change) + `regenerate_link` heal wiring.
- `subscriptions/services/plan_sync.py`, `stripe_client.py` — unchanged (reused as-is).
- `BillingPlanPriceHistory` — reused audit, no model/migration change.
- Tests: `subscriptions/tests.py` (Regenerar heal paths); docs: `docs/stripe-subscriptions.md`.
- No public API, env, or dependency changes. Orphan-price semantics unchanged (log + History row, manual Dashboard cleanup).
