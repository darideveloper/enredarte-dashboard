## Why

The subscription price/product is a `django-solo` singleton (`BillingPlan`) whose
`stripe_product_id` / `stripe_price_id` are stored in the DB row. After a Stripe
account switch (or a deleted/archived price), those stored IDs point at resources
that no longer exist under the current key, so `Generar link de suscripción`
fails with `Stripe no respondió: No such price price_xxx` and there is no
in-product way to regenerate product + price — the only recovery is a manual
django-shell or Dashboard cleanup. Link generation should self-heal instead.

## What Changes

- **Auto-regenerate on `Generar link`** when the checkout (or the stored price)
  is detected as stale: regenerate the Stripe Product + Price from the
  `BillingPlan` row (`amount` / `currency` / `interval`) and retry the checkout
  **once**.
- **Auto-create when `stripe_price_id` is empty** (fresh DB / never configured):
  `Generar link` calls `ensure_stripe_price` instead of refusing with
  "Configura el precio".
- **Force-create product variant** in `get_or_create_product`: when the stored
  `stripe_product_id` no longer resolves in Stripe (account switch), create a
  fresh product instead of re-raising `resource_missing`; skip archiving the
  ghost price.
- **Narrow trigger predicate**: only regenerate on a `resource_missing`
  `InvalidRequestError` referencing the stored `price`/`product`. Authentication /
  permission / network / rate-limit errors **never** regenerate (guards against
  creating products in the wrong account and orphan-price spam).
- **Loud, audited success**: when a heal fires and the retried checkout
  succeeds, show a success message that makes it explicit the price was
  regenerated; the existing `BillingPlanPriceHistory` row records the change.
- **Scoped to `Generar link` only**: `Regenerar link`, `Sincronizar desde
  Stripe` and `Customer Portal` keep their current behavior.
- **Fail-loud on heal failure**: if regeneration succeeds but the retry still
  fails — or regeneration itself fails — show the Stripe error, log the orphan
  `price_xxx`, and do no rollback (manual Dashboard cleanup, as today).

## Capabilities

### New Capabilities
- `auto-price-regeneration`: self-healing regeneration of the shared
  `BillingPlan` Stripe product/price on `Generar link` when the stored
  product/price is missing or unset, with a narrow trigger predicate (which
  provides wrong-account safety — non-staleness errors never regenerate), a
  single forced retry, and loud audited success.

### Modified Capabilities
- `artist-subscription-actions`: `generate_link` alters its failure/empty-price
  behavior to trigger `auto-price-regeneration` instead of a generic
  "Stripe no respondió" / "Configura el precio" refusal. `regenerate_link`,
  `open_portal`, `sync_from_stripe` unchanged.
- `admin-editable-price`: `ensure_stripe_price` gains a force-create path
  (ignore a missing old product, skip archiving a ghost price) and an
  idempotent re-read of the persisted row; still writes
  `BillingPlanPriceHistory`.

## Impact

- `artworks/admin.py` — `generate_link` flow (and its shared checkout helper):
  add heal detection + single retry + loud message.
- `subscriptions/services/plan_sync.py` — `ensure_stripe_price` force-create path.
- `subscriptions/services/stripe_client.py` — `get_or_create_product` force-create.
- `BillingPlanPriceHistory` — audit rows already cover regenerated prices (no model change).
- No DB migrations, no new dependencies, no public API changes.
- Existing `ArtistSubscription` rows pointing at old-account `cus_xxx` / `sub_xxx`
  are **not** migrated; the existing stale-customer recovery heals them per-artist
  on their next action (unchanged).
- Tests: `subscriptions/tests.py` and `artworks/tests.py` (heal-path unit + admin
  endpoint tests).