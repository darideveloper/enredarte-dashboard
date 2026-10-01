## Context

Enredarte monetizes three ways: one-off artwork sales (Stripe), monthly artist subscriptions (Stripe **or** manual cash), and a percentage commission retained/owed on each artwork sale. Today each flow persists only *current state*:

- `ArtworkOrder` (`artworks/models.py`) keeps one row per sale (`amount`, `currency`, `paid_at`, status) — the only flow with usable history.
- `Artist.commission` is a live integer percentage; the split is displayed live in the admin and is never stored per sale.
- `ArtistSubscription` keeps `cash_last_paid_at` (overwritten on every cash confirmation in `artworks/admin.py`) and `raw_state` (the *last* Stripe invoice). Prior subscription payments are lost.
- `BillingPlan` holds the single current plan amount; a price change would retroactively alter any recomputation.

Constraints: Django + Django Unfold admin, Spanish operator UI (see `docs/django-i18n-es-admin.md`), Postgres, no new dependencies desired, public REST API must not leak internal financial data.

## Goals / Non-Goals

**Goals:**
- One append-only ledger of every money movement, queryable by month, date range, artist, kind, payment method, and currency.
- Signed amounts: income positive, artist commissions negative.
- Commission computed from the artist's percentage **at sale time** and frozen into the entry.
- Read-only, auto-populated ledger; exactly one human-editable field (`reconciled`) toggled inline from the list.
- Visible per-currency **income / expense / net** totals for both the filtered view and the full system, in the same list.
- Every admin-visible text in Spanish (`docs/django-i18n-es-admin.md`).
- Backfill existing artwork sales.

**Non-Goals:**
- No currency conversion / FX rates — totals are split per currency.
- No public API or serializer exposure.
- No editing, adding, or deleting ledger entries in the admin (only `reconciled`).
- No audit trail for `reconciled` (plain boolean, per decision).
- No reconstruction of pre-existing cash/online subscription payments (unrecoverable).
- No charting library or finance dependency; no separate monthly report page.
- No change to `ArtworkOrder` / `ArtistSubscription` / `Artist` / `BillingPlan` fields.

## Decisions

### 1. New `finance` app with a single `FinancialEntry` model
- **Decision**: A small dedicated app holding one append-only model `FinancialEntry` (admin section "Finanzas" → "Movimientos").
- **Rationale**: The ledger spans the artwork and subscription domains; a dedicated app gives a clean, centralized home and avoids coupling the model into either feature app.
- **Alternatives**: Model inside `artworks` — rejected: money ledger is not an artwork sub-concept and importing subscription FKs into the artwork domain is awkward. Model inside `core` — rejected: `core` hosts shared plumbing (`StripeEvent`), not a business domain.

### 2. Signed `amount` on one row per economic event
- **Decision**: Each entry carries a signed `amount` (`+` income, `−` expense) plus a `kind` (`artwork_sale`, `artist_commission`, `subscription_payment`). A sale produces **two** rows (income + commission).
- **Rationale**: The product explicitly wants expenses negative and sales/subscriptions positive. A uniform signed field makes totals a plain `Sum`, and filters stay uniform. Two rows per sale keeps income and commission independently filterable (`kind`).
- **Alternatives**: One row per sale with separate `gross`/`commission` columns — rejected: totals and filtering become conditional per kind. Commission recomputed live — rejected: not persisted, breaks historical accuracy.

### 3. Currency is per entry; totals grouped by currency
- **Decision**: Store `currency` (`MXN`/`USD`) on each entry; report totals per currency.
- **Rationale**: Sales may be MXN or USD and the plan is a single currency. Inventing an FX rate risks wrong numbers.
- **Alternatives**: Convert to a single reporting currency — rejected (no reliable rate source). Force MXN only — rejected (drops USD sales).

### 4. Commission frozen at sale time
- **Decision**: When a sale transitions to paid, snapshot `artist.commission` (percentage) and compute the commission amount immediately, storing both on the commission entry.
- **Rationale**: Matches "calculated based on the artist commission percentage, when the sale happens" and prevents later artist edits from rewriting past splits. This intentionally reverses the archived `artist-commission` non-goal about snapshotting.
- **Alternatives**: Recompute live from `Artist.commission` — rejected (retroactive drift).

### 5. Refunds write reversal entries, not deletions
- **Decision**: A refunded/`REFUNDED` order creates a negative `artwork_sale` row and a positive (reverse) `artist_commission` row, so the pair nets to zero while preserving the original event.
- **Rationale**: Append-only integrity, honest totals, traceable history. Covers the double-sale auto-refund backstop already present in `artworks/order_webhooks.py`.
- **Alternatives**: Mutate/void the original rows — rejected (destroys history). Ignore refunds — rejected (inflates income).

### 6. `reconciled` is a plain inline-editable boolean
- **Decision**: Add `reconciled` (default `False`) as the only editable field, exposed via Django's native `list_editable`; no `reconciled_by`/`reconciled_at`.
- **Rationale**: Directly requested; `list_editable` is native (no custom JS). No audit trail was requested.
- **Alternatives**: Custom inline-edit JS — rejected (unnecessary). Audit columns — rejected (explicitly declined).

### 7. Amount snapshot for subscription entries
- **Decision**: Online entries use the Stripe invoice's `amount_paid`/`currency` from the webhook payload; cash entries use `BillingPlan.amount`/`currency` captured at confirmation.
- **Rationale**: Accurate for the period even if the plan price changes later.
- **Alternatives**: Read the current `BillingPlan.amount` live — rejected (historical drift, single currency).

### 8. Admin reporting via native list + injected totals
- **Decision**: `FinancialEntryAdmin` with `date_hierarchy = "occurred_on"` (month drill-down), `list_filter` (`occurred_on` range, `artist`, `kind`, `payment_method`, `currency`, `reconciled`), `list_editable = ["reconciled"]`, everything else readonly, `has_add_permission`/`has_delete_permission` = `False`. Totals are computed in `changelist_view` and rendered via Unfold's native `list_after_template` hook (one small partial), never a full `change_list.html` override.
- **Rationale**: Zero new dependencies; matches the requested "filtered list + totals" and native month drill-down. `list_after_template` renders outside the changelist `<form>` and still renders when the result list is empty, so full-system totals are always visible.
- **Alternatives**: A separate monthly pivot page — rejected (user chose list+totals). `django-admin-charts` — rejected (new dependency). Overriding `change_list.html` — rejected (lazier native hook exists).

### 9. Idempotent, event-keyed entries
- **Decision**: Store a `reference` string tied to the source event (Stripe invoice id, payment intent id, or cash period key) and guard creation so webhook retries and accidental exact-duplicate confirms do not double-book an entry. The guard SHALL be a **partial** unique constraint on (`kind`, `reference`) applied only when `reference` is non-empty, so blank-reference rows (backfill, cash keyed differently) never collide. A refund reversal SHALL use a distinct reference (e.g. the original key suffixed with `-refund`) so it does not collide with the original `artwork_sale` row on the same `kind`.
- **Rationale**: Stripe delivers at-least-once; `apply_paid_transition` is already status-idempotent, but invoice handling needs its own key. A plain unique constraint on (`kind`, `reference`) would break on blank references and on the refund/sale pair, so a partial constraint plus distinct reversal keys is required.
- **Alternatives**: Rely only on `StripeEvent` dedupe — rejected (does not protect the cash path or local re-runs).

### 10. Backfill artwork sales only
- **Decision**: A data migration creates `artwork_sale` + `artist_commission` entries for existing orders with `paid_at`, using the artist's **current** commission percentage; subscription entries begin at go-live.
- **Rationale**: Sale data is reconstructible; overwritten subscription history is not. Using the current commission for backfill is the only available value and is documented in the migration.
- **Alternatives**: No backfill — rejected (loses reconstructible history). Estimate subscriptions — rejected (guesses).

### 11. Filtered total and full-system total in the same footer
- **Decision**: Compute two aggregates in `changelist_view` — one over the filtered changelist (`cl.queryset`, respects month drill-down + all filters) and one over the permission-scoped, unfiltered, all-time base (`cl.root_queryset`) — each grouped per currency and split into income (sum of positive amounts), expenses (sum of negative amounts), and net. Render both in the same totals partial as "Vista actual" and "Total del sistema", with Spanish labels.
- **Rationale**: The admin already exposes both querysets (`ChangeList.__init__` sets `root_queryset = model_admin.get_queryset(request)` and `queryset` = the filtered one), so no extra scoping logic is needed. Two `GROUP BY currency` queries — each with conditional `Sum`s (`filter=Q(amount__gt=0)` for income, `filter=Q(amount__lt=0)` for expenses) — are cheap and give month-vs-all-time context in one screen. Using `root_queryset` (not `model.objects`) keeps any future row-level permission scoping intact.
- **Alternatives**: A separate report page — rejected (user wants one view). A single combined number — rejected (per-currency decision). Denormalized running totals — deferred until volumes justify it.
- **Caveat**: `values("currency").annotate(Sum(...))` can inflate totals if a filter/search introduces a multi-valued join (M2M / reverse FK). Filters and search fields SHALL remain single-valued (FK / choice) fields; add a subquery-based aggregate if that ever changes. The full-system aggregate is the only unbounded query — cache or denormalize it if the table grows large.

## Risks / Trade-offs

- **[Risk] Backfilled commissions use the artist's *current* percentage, which may differ from the historical agreement.** → Mitigation: documented `ponytail:`-style note in the migration; operators can adjust via a follow-up data fix if a known discrepancy exists.
- **[Risk] Mixed-currency totals are not a single number.** → Mitigation: totals explicitly per currency; no misleading consolidation.
- **[Risk] Cash double-confirm intentionally records one payment per click, so an accidental double click books two entries.** → Mitigation: `reference` keyed by the resulting period rejects exact duplicates.
- **[Risk] Historical subscription payments remain incomplete before go-live.** → Mitigation: accepted and documented; only artwork sales are backfilled.
- **[Risk] Money logic is a correctness-sensitive path.** → Mitigation: unit tests per write hook and a reconciliation assertion that a refunded sale's entries net to zero.
- **[Risk] Ledger rows written inside existing webhook/atomic blocks could fail the core transition.** → Mitigation: ledger writes live inside the same transaction as the transition (they must not silently diverge); failures surface and roll back the event for retry.
- **[Risk] A naive `(kind, reference)` unique rule collides on blank references and on the refund/sale pair.** → Mitigation: partial unique constraint applied only to non-empty references, plus distinct reversal references (decision 9).

## Migration Plan

1. Create the `finance` app and `FinancialEntry`; add to `INSTALLED_APPS`.
2. `makemigrations finance` then a data migration backfilling entries from paid `ArtworkOrder`s (idempotent, reversible by deleting ledger rows for the backfill references).
3. `migrate` during a maintenance window (shared Postgres — migrate from a single sibling at a time per `docs/django-worktrees.md`).
4. Deploy the write hooks; new events populate the ledger automatically.
5. Rollback: revert the hooks (ledger becomes inert) and drop the `finance` tables; no other model is touched.

## Open Questions

- None blocking. All decisions (1–11) were confirmed with the user during exploration: currency split, backfill scope, commission snapshot, refund reversals, reconciled flag, actual-amount snapshot, all-time full-system total, income/expense/net breakdown, and Spanish admin labels.
