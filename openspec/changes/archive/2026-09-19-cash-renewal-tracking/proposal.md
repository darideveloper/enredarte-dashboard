## Why

Cash subscriptions are indefinite: once confirmed, an artist stays visible forever with no paid-date, no renew-date, and no reminders. Operators have no way to know when a cash payment lapses, and nothing ever deactivates non-renewing artists — the dashboard silently gives permanent visibility for one payment.

## What Changes

- Add `ArtistSubscription.cash_last_paid_at` (last cash payment date); reuse `current_period_end` as the cash renew date (monthly, like the plan).
- Extend **Confirmar pago** to `active` + `past_due` cash rows: each click stamps a new paid date and pushes the renew date one calendar month from `max(today, current renew)`. First confirm on legacy undated rows initializes both dates.
- Extend **Cancelar efectivo** to `past_due` cash rows.
- Show an "Efectivo" date group (Último pago, Vence, status) in the read-only subscription inline on the Artist page.
- Add a daily `check_cash_renewals` management command (external cron, same precedent as `release_expired_orders`): reminder emails 3 days before renew, "vence hoy" emails on the day, `past_due` + overdue emails after expiry (visible through the plan's 3-day grace via untouched `compute_is_active`), `canceled` + deactivation emails past grace. Skips rows with null renew date; per-artist mail failure logs and continues.
- Add 4 mailer functions + 16 Spanish per-audience templates (reminder, vence-hoy, overdue, deactivated) through existing `notifications.py`.

## Capabilities

### New Capabilities
- `cash-renewals`: monthly renew dates, re-confirm extension, cron-driven reminders/overdue/deactivation for cash rows.

### Modified Capabilities
- `cash-payments`: Confirmar/Cancelar visibility extends to `past_due`; Confirmar performs renew math; re-entering online unchanged.
- `email-notifications`: 3 new senders + per-audience template pairs (reminder, overdue, deactivated).
- `artist-subscription`: new `cash_last_paid_at` field; `current_period_end` doubles as cash renew date.

## Impact

- Affected code: `subscriptions/models.py` (1 field + migration), `artworks/admin.py` (Confirmar/Cancelar logic + gates, inline fields), new `subscriptions/management/commands/check_cash_renewals.py`, `subscriptions/services/notifications.py` (+3 functions), 12 templates, `subscriptions/tests.py`.
- No `compute_is_active` change; no public API change; no new dependencies (calendar-month math in stdlib).
- Deployment needs the daily cron entry; without it, dates pass silently (logged + visible as overdue in admin).
