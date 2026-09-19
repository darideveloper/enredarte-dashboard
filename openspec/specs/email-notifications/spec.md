# email-notifications Specification

## Purpose
Project email infrastructure (SMTP/console settings, central mailer service, per-audience HTML+TXT template convention), first used for cash subscription transition emails to the artist and the admin list.
## Requirements
### Requirement: Email settings and environments
The system SHALL define `EMAIL_BACKEND`, `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS`, `EMAIL_FROM`, and `EMAILS_NOTIFICATIONS` (comma-separated admin recipient list) in `project/settings.py`, following the block documented in `docs/django-project-setup.md:388`. Dev/test environments SHALL default to the console backend (no credentials needed); production SHALL use SMTP with credentials from the environment. `.env.dev.example` and `.env.prod.example` SHALL document all new variables.

#### Scenario: Dev sends to console without credentials
- **WHEN** a cash email fires in the dev environment with no SMTP variables set
- **THEN** the email content SHALL be printed to the runserver console and no network call SHALL occur.

#### Scenario: Tests capture mail in outbox
- **WHEN** any test triggers a cash transition
- **THEN** the emails SHALL be captured via Django's `locmem` backend and assertable through `django.core.mail.outbox` with no extra test dependency.

### Requirement: Central cash mailer service
The system SHALL provide `subscriptions/services/notifications.py` as the only module that sends mail, exposing `send_cash_pending(artist, actor)`, `send_cash_active(artist, actor)`, and `send_cash_canceled(artist, actor)`. Each function SHALL send two separate `EmailMultiAlternatives` messages (TXT + HTML alternatives): an artist receipt (`to=[artist.email]`, artist body) and an admin notice (`to=EMAILS_NOTIFICATIONS`, subject prefixed `[Enredarte]`, naming the artist, dedicated operational body). Each function SHALL log a warning and skip the admin send when `EMAILS_NOTIFICATIONS` is empty. All subjects, bodies, and the `[Enredarte]` prefix SHALL be Spanish, consistent with the admin language.

Exact subjects (artist receipt / admin notice):
- pending: "Tu registro de pago en efectivo está pendiente" / "[Enredarte] Artista marcado como efectivo — {artista}"
- active: "Tu pago en efectivo fue confirmado" / "[Enredarte] Pago en efectivo confirmado — {artista}"
- canceled: "Tu suscripción en efectivo fue cancelada" / "[Enredarte] Suscripción en efectivo cancelada — {artista}"

#### Scenario: Confirm sends artist receipt and admin notice
- **WHEN** `send_cash_active(artist, actor)` runs with two configured admin addresses
- **THEN** exactly two messages SHALL be sent: one to the artist and one to both admin addresses, each with TXT and HTML bodies.

#### Scenario: Empty admin list skips admin send with warning
- **WHEN** `send_cash_active(artist, actor)` runs with `EMAILS_NOTIFICATIONS` empty
- **THEN** only the artist receipt SHALL be sent and a warning SHALL be logged naming the missing configuration.

### Requirement: Email templates per cash transition
The system SHALL ship paired artist templates `subscriptions/templates/subscriptions/email/cash_{pending,active,canceled}.html` and `.txt` plus paired admin templates `cash_{pending,active,canceled}_admin.html` and `.txt`, all sharing the same context (`artist`, `plan`, `actor`, `site/host`). HTML SHALL be the primary body with TXT as fallback alternative. Every artist template SHALL be written fully in Spanish and SHALL contain: a greeting naming the artist, a one-line explanation of the transition (registered / confirmed / canceled), the visibility consequence (hidden until payment is confirmed / now visible / no longer visible), and a reply/contact line. Every admin template SHALL be written fully in Spanish with an operational tone and SHALL contain: the artist's name and email, the transition and its visibility consequence, the acting operator (`actor_name`), and a direct link to the artist's admin change page (`host` + `artist.pk`). Future notification types SHALL follow the same per-audience-template-pair convention without new settings plumbing.

#### Scenario: Every cash email has HTML and text bodies
- **WHEN** any cash email is sent
- **THEN** the message SHALL contain both a `text/plain` and a `text/html` alternative rendering the same information.

#### Scenario: Template copy is Spanish with required elements
- **WHEN** any artist cash template (HTML or TXT) is rendered
- **THEN** the output SHALL contain the artist's name, the transition explanation, the visibility consequence, and a contact line, all in Spanish, with no English fallback strings.

#### Scenario: Admin template carries operational context
- **WHEN** any admin cash template (HTML or TXT) is rendered
- **THEN** the output SHALL contain the artist's name and email, the transition with its visibility consequence, the operator name, and an `/admin/artworks/artist/<id>/change/` link, all in Spanish, with no greeting and no English fallback strings.

### Requirement: Email failure never blocks state changes
Cash admin actions SHALL treat email as a best-effort side effect: if sending raises, the action SHALL log the exception, keep the already-persisted status/`is_active` change, and show `messages.warning` ("Estado guardado, pero el correo falló…") instead of `messages.success`. No cash transition SHALL roll back due to mail failure.

#### Scenario: SMTP outage keeps confirmed payment
- **WHEN** "Confirmar pago" executes while the SMTP server is unreachable
- **THEN** `status` SHALL still become `"active"` with `is_active=True`, the failure SHALL be logged, and the operator SHALL see a warning (not an error, not a 500).

### Requirement: Renewal mailers and templates
The system SHALL expose `send_cash_reminder(artist, actor=None)`, `send_cash_duetoday(artist, actor=None)`, `send_cash_overdue(artist, actor=None)`, and `send_cash_deactivated(artist, actor=None)` in `subscriptions/services/notifications.py`, each sending artist + admin `EmailMultiAlternatives` (TXT + HTML) with the same Spanish per-audience convention and empty-list warning as the transition senders. Exact subjects (artist / admin): reminder `"Tu suscripción vence en 3 días"` / `"[Enredarte] Suscripción por vencer — {artista}"`; duetoday `"Tu suscripción vence hoy"` / `"[Enredarte] Suscripción vence hoy — {artista}"`; overdue `"Tu pago está vencido"` / `"[Enredarte] Pago vencido — {artista}"`; deactivated `"Tu suscripción fue desactivada por falta de pago"` / `"[Enredarte] Artista desactivado por no renovar — {artista}"`. Bodies SHALL come from new `cash_reminder[_admin]`, `cash_duetoday[_admin]`, `cash_overdue[_admin]`, `cash_deactivated[_admin]` template pairs (16 files): artist bodies carry greeting + what is due + renew date + contact line; admin bodies carry name + email + state + operator (cron: "proceso automático") + admin change-page link.

#### Scenario: Reminder carries the renew date
- **WHEN** `send_cash_reminder` runs
- **THEN** both artist alternatives SHALL contain the renew date and the message SHALL NOT change any state.

#### Scenario: Deactivation notice names the cause
- **WHEN** `send_cash_deactivated` runs
- **THEN** the artist body SHALL state the deactivation was for non-renewal and how to reactivate, and the admin body SHALL name the automatic process as actor.
