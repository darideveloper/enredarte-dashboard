## ADDED Requirements

### Requirement: Renewal mailers and templates
The system SHALL expose `send_cash_reminder(artist, actor=None)`, `send_cash_duetoday(artist, actor=None)`, `send_cash_overdue(artist, actor=None)`, and `send_cash_deactivated(artist, actor=None)` in `subscriptions/services/notifications.py`, each sending artist + admin `EmailMultiAlternatives` (TXT + HTML) with the same Spanish per-audience convention and empty-list warning as the transition senders. Exact subjects (artist / admin): reminder `"Tu suscripción vence en 3 días"` / `"[Enredarte] Suscripción por vencer — {artista}"`; duetoday `"Tu suscripción vence hoy"` / `"[Enredarte] Suscripción vence hoy — {artista}"`; overdue `"Tu pago está vencido"` / `"[Enredarte] Pago vencido — {artista}"`; deactivated `"Tu suscripción fue desactivada por falta de pago"` / `"[Enredarte] Artista desactivado por no renovar — {artista}"`. Bodies SHALL come from new `cash_reminder[_admin]`, `cash_duetoday[_admin]`, `cash_overdue[_admin]`, `cash_deactivated[_admin]` template pairs (16 files): artist bodies carry greeting + what is due + renew date + contact line; admin bodies carry name + email + state + operator (cron: "proceso automático") + admin change-page link.

#### Scenario: Reminder carries the renew date
- **WHEN** `send_cash_reminder` runs
- **THEN** both artist alternatives SHALL contain the renew date and the message SHALL NOT change any state.

#### Scenario: Deactivation notice names the cause
- **WHEN** `send_cash_deactivated` runs
- **THEN** the artist body SHALL state the deactivation was for non-renewal and how to reactivate, and the admin body SHALL name the automatic process as actor.
