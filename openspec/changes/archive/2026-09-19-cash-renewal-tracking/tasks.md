## 1. Data model

- [x] 1.1 Add `cash_last_paid_at` (nullable date, Spanish labels) + migration.
- [x] 1.2 Add month-add helper (stdlib, month-end clamp) + unit tests (Jan 31 → Feb 28, leap year, mid-month).

## 2. Admin actions

- [x] 2.1 Confirmar: allow `active`/`past_due`, renew math (`max(today, renew) + 1 month`, init when null), re-send receipt; update permission gate.
- [x] 2.2 Cancelar: allow `past_due`; update permission gate.
- [x] 2.3 Inline "Efectivo" group (Último pago, Vence, status); update `ArtistSubscriptionAdmin` readonly view.
- [x] 2.4 Admin tests: re-confirm extends + receipt re-sent; grace recovery past_due→active; cancel during grace; double-confirm now extends (update old no-op test); visibility matrix incl. past_due.
- [x] 2.5 Cycle resets: Marcar clears both dates on canceled rows; Generar online-reset clears `cash_last_paid_at`; tests for both.

## 3. Cron command

- [x] 3.1 Add `check_cash_renewals` (remind-3/vence-hoy/past_due/deactivate/skip-null, per-artist try/except, summary log).
- [x] 3.2 Command tests with frozen dates for every branch + failure-continues-batch.

## 4. Emails

- [x] 4.1 Add `send_cash_reminder/duetoday/overdue/deactivated` + 16 templates (exact Spanish subjects, per-audience bodies).
- [x] 4.2 Mailer tests via `outbox` (recipients, alternatives, subjects, renew date in reminder, actor in admin bodies).

## 5. Verification

- [x] 5.1 `manage.py check` + full `subscriptions`/`artworks` suites green.
- [x] 5.2 Dev console pass: confirm → renew dates visible; run command across staged dates; cleanup.
- [x] 5.3 Docs: renewal section in `stripe-subscriptions.md` + cron entry documented.
