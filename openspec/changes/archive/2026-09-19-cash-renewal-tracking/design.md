## Context

Cash rows today: `payment_method=cash`, indefinite `active`, `current_period_end` always empty, `last_synced_at` per transition. `compute_is_active()` already maps `past_due` → visible until `current_period_end + BillingPlan.grace_period_days` (3). Scheduling precedent: `artworks/management/commands/release_expired_orders.py` as external cron entrypoint; no Celery/beat. Decisions from brainstorming: monthly period, re-confirm extends, remind-then-deactivate, reuse plan grace.

## Goals / Non-Goals

**Goals:**
- Every cash payment produces a visible paid date + renew date; operators always know who owes renewal.
- Reminders before expiry; automatic, notified deactivation past grace.
- Zero new statuses, zero `compute_is_active` change, zero new dependencies.

**Non-Goals:**
- No payment ledger/amounts; no per-artist custom periods; no in-process scheduler; no SMS/WhatsApp (email only).

## Decisions

### D1: Reuse `current_period_end` as the renew date; one new field
`cash_last_paid_at` records the paid date; `current_period_end` (empty for cash today, already displayed in the inline) becomes the renew date. Alternative (dedicated `cash_renews_at`): rejected — duplicates a displayed field and would bypass the free `past_due` grace math.
Renew math: base = `max(today, current renew date-part)` + 1 calendar month, same-day-next-month with month-end clamp, stored end-of-day (23:59 project timezone) since `current_period_end` is a `DateTimeField`; all cron day-comparisons use date parts in the project timezone. stdlib only (no dateutil). The 23:59 storage aligns the cron's strict `today > renew + grace` cancel boundary with the evening `compute_is_active` already produces.

### D2: Confirmar/Cancelar extend to `past_due`
Paying during grace must recover to `active`; manual cancel during grace must stay possible. Confirmar on `active`/`past_due` stamps paid date, pushes renew, sets `active`, re-sends the confirmation receipt (each click = one monthly payment). Visibility matrix enforced at render + permission boundary (403), as established.

### D3: Daily idempotent cron command
`check_cash_renewals`: renews-in-3 → reminder; renews-today → vence-hoy; expired + active → `past_due` + overdue emails; past-grace + past_due → `canceled` + `is_active=False` + deactivation emails. Reminder idempotency by date equality (daily cron assumed); deactivation state-based so a missed day still catches up. Null-renew rows skipped (legacy until next Confirmar). Per-artist try/except: log + continue, summary line logged.

### D4: 4 new mail events, per-audience pairs
`reminder` / `duetoday` / `overdue` / `deactivated` via `notifications.py` (`send_cash_reminder/duetoday/overdue/deactivated`), artist + admin HTML/TXT pairs (16 files), Spanish, subjects `"Tu suscripción vence en 3 días"` / `"Tu suscripción vence hoy"` / `"Tu pago está vencido"` / `"Tu suscripción fue desactivada por falta de pago"` with `[Enredarte] … — {artista}` admin variants.

## Risks / Trade-offs

- [Risk] Cron never configured → silent lapse → Mitigation: per-run summary log + visibly overdue "Vence" in admin; cron entry documented as a deploy step.
- [Risk] Cron misses a day → that day's reminder skipped → Mitigation: accepted; deactivation is state-based and self-heals.
- [Risk] Clock/TZ skew → reminders a day off → Mitigation: single project-TZ date comparison everywhere.
- [Trade-off] Re-confirming early extends from current renew (not paid date) → operators can stack months by repeated clicks → accepted (each click sends a receipt; matches "each click = one payment").
- [Risk] A stuck `past_due` cash row has no sync-style refresh — Confirmar/Cancelar are the only resolution paths (sync stays 403 for cash, by design) → Mitigation: stated explicitly so operators don't wait for a re-sync that can't come.

## Migration Plan

1. Deploy code; run migration (nullable field, zero rewrite).
2. Add daily cron entry for `check_cash_renewals`.
3. Verify: targeted tests, console-backend dry run, inline shows dates.
4. Rollback: revert code + migrate back; cron entry harmless without the command (remove it too).

## Open Questions

- Reminder lead: 3 days (default, symmetric with grace).
- "Vence hoy": separate email (default) or folded into the reminder.
