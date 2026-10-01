## Why

Enredarte has no historical record of money movements. Artwork sales persist only as their current `ArtworkOrder` state, artwork commissions are never stored (computed live from the artist's current percentage), and subscription payments keep only the *last* cash date or *last* Stripe invoice — every prior month is overwritten. As a result, a month-by-month revenue/expense report cannot be produced retroactively, and editing an artist's commission silently rewrites the split of every past sale. Operators need one centralized, filterable, auto-calculated view of every payment and commission with visible totals.

## What Changes

- Introduce an append-only **financial ledger** (`finance` app, `FinancialEntry` model) recording one immutable row per economic event, with a **signed amount** convention: income positive (`+`), artist commissions negative (`−`).
- Record ledger entries automatically at the existing event points, never by hand:
  - Artwork sale paid → `+artwork_sale` (gross) and `−artist_commission` (snapshot of `artist.commission%` at sale time).
  - Artwork order refunded → reversal entries (negate the sale, reverse the commission).
  - Stripe `invoice.payment_succeeded` → `+subscription_payment` using the invoice's actual `amount_paid`/`currency`.
  - Cash "Confirmar pago" → `+subscription_payment` snapshotting `BillingPlan.amount`/`currency` at confirmation.
- Add a `reconciled` boolean on every entry — the only human-editable field — editable inline from the admin list.
- Add a read-only **"Finanzas" admin section** with month drill-down, custom filters (date range, artist, kind, payment method, currency, reconciled), and per-currency **income / expense / net** totals for **both the currently filtered view and the full system** shown in the same list.
- Backfill existing paid `ArtworkOrder` rows into the ledger. Subscription entries start from go-live (old cash/invoice history is unrecoverable).
- Keep the ledger and the commission calculation strictly internal: no public REST/API exposure (consistent with the existing `commission` field).

## Capabilities

### New Capabilities

- `financial-ledger`: the append-only signed ledger model, per-currency amounts, the write hooks on artwork-sale / refund / Stripe-invoice / cash-confirmation events, the sale-time commission snapshot, the `reconciled` marker, and the backfill of historical artwork sales.
- `finance-admin`: the fully-Spanish read-only "Finanzas" admin list (`Movimientos`), month drill-down, filters, per-currency income / expense / net totals for both the filtered view and the full system, and the inline `reconciled` toggle.

### Modified Capabilities

- None. Ledger writes are a new concern added alongside existing flows and are defined entirely by `financial-ledger`; no existing spec requirement changes.

## Impact

- New Django app `finance` (`models.py`, `admin.py`, `apps.py`, `migrations/`) with `verbose_name="Finanzas"`, registered in `project/settings.py` `INSTALLED_APPS`, plus a "Finanzas" entry in the Unfold sidebar navigation (`UNFOLD["SIDEBAR"]` in `project/settings.py`).
- Write hooks in `artworks/services.py` (`apply_paid_transition`), `artworks/order_webhooks.py` and `artworks/services.py` (double-sale refund), `subscriptions/webhooks.py` (`_handle_invoice_payment_succeeded`), and the cash confirm action in `artworks/admin.py`.
- One data migration backfilling `FinancialEntry` rows from existing paid `ArtworkOrder`s.
- No new Python dependencies. No public API, serializer, or customer-facing change. No change to `ArtworkOrder`, `ArtistSubscription`, `Artist`, or `BillingPlan` schemas.
- Totals are grouped per currency; no exchange-rate conversion is introduced.
