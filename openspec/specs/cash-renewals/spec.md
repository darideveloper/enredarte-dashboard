# cash-renewals Specification

## Purpose
Monthly renew dates, re-confirm extension, and cron-driven reminders/overdue/deactivation for manual cash subscriptions.
## Requirements
### Requirement: Cash paid date and renew date
The system SHALL provide `ArtistSubscription.cash_last_paid_at` (nullable date, Spanish `verbose_name="Último pago en efectivo"` + `help_text`) and SHALL use `current_period_end` as the cash renew date. Confirmar pago on a cash row SHALL stamp `cash_last_paid_at = today` and set `current_period_end` to end-of-day (23:59 project timezone) on `max(today, current renew date-part) + 1 calendar month` (same-day-next-month, month-end clamped, no new dependencies; all comparisons use date parts in the project timezone since `current_period_end` is a `DateTimeField`). The first confirm on a legacy row with null renew date SHALL initialize both dates. Both dates SHALL render read-only in the subscription inline's "Efectivo" group.

#### Scenario: Confirm pushes renew one month from the later date
- **WHEN** an operator confirms cash payment for a cash-`active` row renewing in 10 days
- **THEN** `cash_last_paid_at` SHALL be today and `current_period_end` SHALL be the previous renew date + 1 calendar month (not today + 1 month).

#### Scenario: Legacy undated row initializes on confirm
- **WHEN** an operator confirms a cash row with null `current_period_end`
- **THEN** both dates SHALL initialize (paid = today, renew = end-of-day today + 1 calendar month).

#### Scenario: Renew math clamps month-ends
- **WHEN** the base date is January 31
- **THEN** the renew date SHALL be February 28 (or 29 in leap years), never March.

### Requirement: Daily renewal check command
The system SHALL provide a `check_cash_renewals` management command (external cron entrypoint, daily) that, for cash rows with non-null renew date, using one project-timezone date (`today`, compared against `current_period_end` date parts): sends reminder emails when renew is in 3 days; sends vence-hoy emails when renew is today; sets `past_due` + sends overdue emails when expired (`today > renew date`) and still `active`; sets `canceled` + `is_active=False` + sends deactivation emails when strictly past grace (`today > renew date + grace_period_days`) and `past_due` — aligned with `compute_is_active`, which hides the artist from the renew evening onward. The command SHALL invoke mailers with `actor="proceso automático"`. Rows with null renew date SHALL be skipped. Each artist SHALL be processed in try/except (log + continue); the command SHALL log a summary line with counts.

#### Scenario: Reminder before expiry
- **WHEN** the command runs and a cash-`active` row renews in exactly 3 days
- **THEN** reminder emails SHALL be sent to the artist and the admin list, with no state change.

#### Scenario: Expiry flips to past_due, still visible
- **WHEN** the command runs and a cash-`active` row's renew date is past
- **THEN** `status` SHALL become `"past_due"` (visible through grace via unchanged `compute_is_active`), overdue emails SHALL be sent, and the confirmation receipt SHALL NOT be re-sent.

#### Scenario: Past grace deactivates with notice
- **WHEN** the command runs and a cash-`past_due` row is past `current_period_end + grace_period_days`
- **THEN** `status` SHALL become `"canceled"`, `Artist.is_active` SHALL become `False`, and deactivation emails SHALL be sent.

#### Scenario: Null renew date skipped
- **WHEN** the command runs and a cash row has null `current_period_end`
- **THEN** the row SHALL be left untouched and counted as skipped in the summary.

#### Scenario: Per-artist mail failure continues batch
- **WHEN** sending for one artist raises
- **THEN** the failure SHALL be logged, that artist SHALL keep its computed state, and the command SHALL continue with the next artist.

### Requirement: Cycle resets clear stale dates
Re-marking a cash-`canceled` row via Marcar como efectivo SHALL clear `cash_last_paid_at` and `current_period_end` (fresh pending cycle with no inherited dates). Re-entering the online flow via Generar link SHALL clear `cash_last_paid_at` (the Stripe flow owns `current_period_end` from then on).

#### Scenario: Re-mark starts dateless
- **WHEN** an operator marks a cash-`canceled` row (old paid/renew dates present) as cash again
- **THEN** both date fields SHALL be empty until the next Confirmar initializes them, and the cron SHALL keep skipping the row meanwhile.
