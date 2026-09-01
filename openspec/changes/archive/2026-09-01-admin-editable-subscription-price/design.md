## Context

The current `BillingPlan` (django-solo singleton) is the only source of truth for the artist-subscription price. Today it stores a single `stripe_price_id` field that the operator has to obtain by hand from the Stripe Dashboard, plus an informational `currency` (no amount, no interval). The id is also seeded from the `STRIPE_PRICE_ID` env var at boot via `default_stripe_price_id()`.

The operator experience is broken in three concrete ways:

1. **Editing the price requires leaving the app.** Changing the price is a multi-step manual ritual: log into the Stripe Dashboard, create a new Price (Stripe Prices are immutable), copy the `price_xxx`, paste it into the `BillingPlan` form (or set `STRIPE_PRICE_ID` and redeploy).
2. **No amount/currency/interval is stored locally.** The form just takes a Stripe id, so the admin has no way to confirm what the artist is being charged without fetching the price back from Stripe.
3. **No audit trail of price changes.** The `BillingPlan` row only ever shows the current state; historical prices are nowhere in the local DB (they live in Stripe's dashboard, scrolled to oblivion).

The webhook and link-generation flows already treat `BillingPlan.stripe_price_id` as the single source of truth at the moment a Checkout Session is created (`artworks/admin.py:408`). The change is local to the `BillingPlan` admin and its supporting service code — webhooks, `ArtistSubscription`, and the public landing pages are untouched.

## Goals / Non-Goals

**Goals:**
- Replace the manual `stripe_price_id` field with friendly form fields (`amount`, `currency`, `interval`).
- Auto-manage `stripe_product_id` and `stripe_price_id` behind the scenes: the app talks to Stripe, the operator never types a Stripe id.
- Make a price change atomic from the operator's point of view: edit three numbers, click save, the new price is live for new sign-ups.
- Preserve existing subscribers (Stripe's standard behavior — existing subscriptions are never re-priced by replacing their price).
- Persist an append-only `BillingPlanPriceHistory` so the operator can see "what price was active when this artist signed up" without scraping the Stripe dashboard.
- Fail loudly on Stripe errors during save — no half-written DB rows.
- Show a read-only "Confirmado por Stripe" line on the change form so the operator can verify the DB matches Stripe before editing.

**Non-Goals:**
- Multiple plans / tiers (the django-solo singleton stays; this is already explicit in `billing-plan/spec.md`).
- New env vars (the `STRIPE_PRICE_ID` env var is kept as a documented first-time seed only).
- Renaming the Stripe product from the admin (the product name is whatever was set in the Stripe Dashboard, or `Membresía Enredarte` for new products).
- Currencies beyond `MXN` and `USD` (dropdown is restricted).
- Intervals beyond `month` (single choice today).
- Migrating existing artists to a new price automatically (existing subscriptions are intentionally untouched).
- A management command to reconcile / re-bootstrap (could be a follow-up; not needed for the current change).

## Decisions

### D1. New `BillingPlan` fields and what they replace

**Decision:** Remove the editable `stripe_price_id` field. Add `amount` (DecimalField, `max_digits=8, decimal_places=2`), `currency` (CharField, choices `[("MXN","MXN"),("USD","USD")]`, default `"MXN"`), `interval` (CharField, choices `[("month","Mensual")]`, default `"month"`), `stripe_product_id` (CharField, blank, auto-managed), `stripe_price_id` (CharField, blank, auto-managed — same field name as today but no longer editable by the operator), `last_synced_stripe_at` (DateTimeField, null, auto-managed).

**Why:** The operator must be able to see and edit the three numbers that define the price without going to Stripe. The auto-managed fields keep the existing webhook/link-generation code unchanged (`plan.stripe_price_id` is still the right name to pass to `create_checkout_session`).

**Alternatives considered:**
- *Keep `stripe_price_id` editable as a power-user override.* Adds an "advanced" section to the form. Rejected: more surface for confusion ("which one wins?") and the operator no longer has to think about Stripe ids at all.
- *Store the full Stripe Price object as JSON.* Tempting (everything in one place), but harder to query/index and goes against the project's pattern of keeping Stripe as the source of truth and the DB as a thin mirror.

### D2. Auto-managed price means a new Stripe Price on every change

**Decision:** When `amount`, `currency`, or `interval` changes on save, the app calls `stripe.Price.create` for the new (currency, amount, interval) and stores the returned `price_xxx` on `BillingPlan.stripe_price_id`. Before archiving, it repoints the product's `default_price` to the new price via `stripe.Product.modify(product_id, default_price=new_price_id)` — Stripe blocks `Price.modify(old, active=False)` when `Product.default_price == old_price` (Dashboard-created products have this set). The old `price_xxx` is then archived via `stripe.Price.modify(old_id, active=False)`. The same Stripe product (`prod_xxx`) is reused for every new price. (`stripe.Price.update` is an alias; `modify` is canonical.)

**Why:** Stripe Prices are immutable — there is no API to change `unit_amount` on an existing `price_xxx`. Creating a new price is the only way to change what new sign-ups are charged. Archiving the old price (a) keeps the Stripe dashboard tidy, and (b) prevents an accidental future code path from passing an outdated `price_xxx` to `create_checkout_session`. Reusing the same product keeps the price list under one Stripe dashboard view (a standard Stripe pattern).

**Alternatives considered:**
- *Don't archive the old price.* The Stripe dashboard accumulates prices, but the operator might accidentally wire an old id back in if we ever expose a selector. Archiving is the safer default.
- *Create a new product per amount.* Clean dashboard, but product list grows unbounded. Rejected: a single product with a price list is the idiomatic Stripe pattern for a membership.
- *Make archival a checkbox.* Adds form surface; we'd have to remember a default. Rejected: archiving is unambiguously the safer default.

### D3. Stripe-down behavior = fail loudly

**Decision:** If any Stripe call (`Product.create`, `Price.create`, `Price.update`, `Price.retrieve` for the preview) raises `stripe.error.StripeError` (or a network-level error), the `BillingPlan` save aborts. No `BillingPlan` row, no `BillingPlanPriceHistory` row, no `stripe_price_id` mutation — the operator sees an admin error message and the form is re-displayed with their values intact.

**Why:** Half-written state ("DB claims MXN 349 but Stripe still has 299") is the worst possible failure mode for a billing system. The operator can always retry. The read-only preview fetch failure is the one exception — it must not block the form (preview is informational).

**Alternatives considered:**
- *Two-step save (local first, Stripe later).* More forgiving but you can end up with `stripe_price_id=""` and `amount=349` in the DB, which is exactly the inconsistency we want to avoid. The user explicitly chose "fail loudly" in the exploration.

### D4. New `BillingPlanPriceHistory` model

**Decision:** Append-only audit table. Fields: `billing_plan` (FK to `BillingPlan`, CASCADE), `old_stripe_price_id` (CharField, blank), `new_stripe_price_id` (CharField), `amount` (DecimalField), `currency` (CharField, 3), `interval` (CharField, 10), `old_price_archived` (BooleanField, default `True`), `changed_at` (DateTimeField, `auto_now_add=True`), `changed_by` (FK to `AUTH_USER_MODEL`, null, `SET_NULL`). Rendered as a read-only inline on the `BillingPlan` change page (most-recent first).

**Why:** A future "what price was active when this artist signed up" question is otherwise unanswerable without scraping Stripe. The table is small (one row per price change, ever) and the inline is cheap to render. The user explicitly chose to include history.

**Alternatives considered:**
- *No history table, rely on `StripeEvent`.* `StripeEvent` is the webhook audit log, not a config audit log. Webhook events don't capture "the operator changed the amount from 299 to 349" — that happens in our admin, not on Stripe. Rejected.
- *History inside `BillingPlan` (e.g. a JSONField on the singleton).* Works, but harder to display as a list and to query. A flat table is the cleaner pattern.

### D5. Read-only "Confirmado por Stripe" preview on form load

**Decision:** `BillingPlanAdmin.change_view` does `stripe.Price.retrieve(plan.stripe_price_id)` on GET. If it succeeds, the change form renders a read-only line `Confirmado por Stripe: <amount> <currency> / <interval> (<stripe_price_id>)` via the `extra_context` mechanism. If the call fails, the line is absent — no exception bubbles up.

**Why:** A drift check ("the form says 349 but the artist got charged 299") is cheap to do and prevents a whole class of support tickets. The call is a single GET; Stripe's caching makes it fast.

**Alternatives considered:**
- *No preview.* Cheaper, simpler, but the operator has to flip to the Stripe Dashboard to verify before saving. That's the friction we're trying to remove.
- *Server-side `stripe.Price.retrieve` per request as a hard requirement.* Too brittle — a transient Stripe outage would break the admin page itself.

### D6. First-time seed from `STRIPE_PRICE_ID` env var (kept)

**Decision:** The data migration does a best-effort `stripe.Price.retrieve(settings.STRIPE_PRICE_ID)` and, on success, fills `amount` / `currency` / `interval` / `stripe_product_id` / `stripe_price_id` from the result. If the env var is missing, the API key is missing, or the call raises any exception, the row is left with `amount=0` and the operator must save the form once. After migration, no code path reads `STRIPE_PRICE_ID` at runtime — the DB row is the source of truth.

**Why:** Backwards-compatible: existing deploys (`.env.dev`, `.env.prod`) keep working without any change. New deploys can either set `STRIPE_PRICE_ID` and let the migration seed them, or leave it empty and configure via the admin. The user explicitly chose to keep the env var as a documented first-time seed.

**Alternatives considered:**
- *Remove `STRIPE_PRICE_ID` entirely.* Cleaner, but breaks first-time setup (admin must save the form once before any link works). The user chose to keep the env var.
- *100% offline migration (no Stripe call).* Safe but means the operator always has to type the amount/currency in by hand. The best-effort online path is strictly more convenient when Stripe is reachable.

### D7. `BillingPlanForm.clean()` enforces amount/currency/interval validity

**Decision:** Form-level validation: `amount > 0`, `currency ∈ {MXN, USD}`, `interval == "month"`. The admin's `save_model` does not start the Stripe sync if `form.is_valid() == False`. This is the only validation path — the model itself does not enforce `amount > 0` (we keep the column nullable/0-tolerant so the migration can leave `amount=0` until the operator saves the form).

**Why:** Validation in the form is the project's standard pattern (see `artworks/admin.py`, the Unfold custom forms). Putting it in the model would break the migration's "leave `amount=0` if Stripe is unreachable" path.

### D8. `_billing_blocked` in `artworks/admin.py` simplifies

**Decision:** Drop the `currency` and `interval` checks (they're now enforced at form time, before any Stripe call can succeed). Keep the `is_active_for_new_signups=False` and empty `stripe_price_id` checks. The error message for an empty `stripe_price_id` becomes "Configura el precio (monto y moneda) en Plan de suscripción antes de generar links."

**Why:** `_billing_blocked` exists to short-circuit link generation when the plan isn't ready. Now that "the plan is ready" implies `stripe_price_id` is set (because the form won't save otherwise), the `currency` / `interval` checks there are dead code.

## Risks / Trade-offs

- **R1: Operator changes amount and existing subscribers are unaffected** → documented explicitly in `docs/stripe-subscriptions.md` ("What happens to existing subscribers" callout). No mitigation needed beyond the docs; this is the desired Stripe behavior.
- **R2: Save depends on Stripe being reachable** → fail-loudly (D3). If Stripe is in an outage, no admin save is possible; that's the cost of a single source of truth.
- **R3: First-time migration requires `STRIPE_PRICE_ID` to be set for the auto-seed** → if it isn't, the row is left with `amount=0` and the operator must save the admin form once. Operator-visible behavior is well-defined; no silent failure.
- **R4: Race condition between two operators editing the same `BillingPlan`** → standard last-writer-wins. The django-solo singleton has no row-level locking; a simultaneous save could create two Stripe Prices. Mitigation: Unfold admin already serializes per-user form interactions and a price change is a low-frequency operation. We can revisit with `select_for_update` in a follow-up if it ever matters in practice.
- **R5: Archiving an old price breaks any external code that was holding the `price_xxx`** → the only consumer of `price_xxx` in this codebase is the link-generation flow, which always reads the current `BillingPlan.stripe_price_id`. Existing Stripe Subscriptions are not affected by `active=False` on the price (Stripe keeps billing existing subscriptions on archived prices). Documented in the "What happens to existing subscribers" callout.
- **R6: `stripe.Price.retrieve` on every change-form load adds a Stripe round-trip** → one GET per page load; Stripe's edge cache makes it sub-100 ms in practice. If it ever becomes a problem, switch to a short-lived cache (e.g. 60 s) keyed on `stripe_price_id`.
- **R7: `last_synced_stripe_at` is not auto-updated on `retrieve_price` (only on write-side operations)** → by design; the field is meant to mark the last time we *wrote* to Stripe from this app, not the last time we read. The docs will note this.
- **R8: Renaming the Stripe product from the admin is out of scope** → if the operator renames `name` on `BillingPlan`, the Stripe product keeps its old name. This is documented as out of scope; a follow-up could add a `product_name` field that calls `stripe.Product.modify`.
- **R9: New Stripe price is orphaned if the post-create Stripe calls fail** → if `stripe.Price.create` succeeds and `stripe.Product.modify(product, default_price=new)` or `stripe.Price.modify(old, active=False)` then fails, the DB stays clean (no `BillingPlan` write, no history row, per D3) but the newly-created Stripe price is now an orphan — not referenced by any local `BillingPlan` (and if `Product.modify` succeeded, the product's `default_price` now points at the orphan). The operator sees a Stripe-down error and can retry (retry creates a second orphan). A possible follow-up is to wrap the post-create calls in a `try/except` that archives the new price on failure or a `reconcile` management command. Out of scope for v1. Rare (same network path).

## Migration Plan

1. **Pre-deploy (no action required for existing installs).** No code changes before migration.
2. **`python manage.py migrate subscriptions` runs the data migration.** It adds the new fields with safe defaults, attempts a best-effort `stripe.Price.retrieve(STRIPE_PRICE_ID)` to seed them, and (only on success) preserves the existing `stripe_price_id`. On any failure, `amount` is `0` and the operator must save the admin form once.
3. **Operator saves the admin form** (if step 2 couldn't reach Stripe). The first save will create a new Stripe Price, store the id, and the link-generation flow starts working.
4. **Rollback strategy.** Standard Django reverse migration: `migrate subscriptions 0003_alter_billingplan_stripe_price_id` removes the new fields and the history table; the old `stripe_price_id` field returns. Any new Stripe Prices created during the brief window this change was live remain in Stripe (archived or not, depending on the rollback timing); they are not deleted. The original `price_xxx` (the one referenced by `STRIPE_PRICE_ID`) is unaffected if we never archived it; if we did archive it, set `active=True` again from the Stripe Dashboard.
5. **Side effects on production data.** None for existing subscribers: Stripe never re-prices an existing subscription just because the price the operator used is now archived. Only new sign-ups (new Checkout Sessions) use the new price. The Stripe dashboard will show a list of (archived) old prices under the product; this is intentional.

## Open Questions

None — all 8 design questions from the planning phase were answered. The only remaining minor items (e.g. whether to also rename the product) are explicitly out of scope per the user's answers.
