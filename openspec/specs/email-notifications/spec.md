# email-notifications Specification

## Purpose
Project email infrastructure (SMTP/console settings, central mailer service, per-audience HTML+TXT template convention), first used for cash subscription transition emails to the artist and the admin list.
## Requirements
### Requirement: Email settings and environments
The system SHALL define `EMAIL_BACKEND`, `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS`, `EMAIL_USE_SSL`, `EMAIL_FROM`, and `EMAILS_NOTIFICATIONS` (comma-separated admin recipient list) in `project/settings.py`, following the block documented in `docs/django-project-setup.md:388`. `EMAIL_USE_TLS` SHALL default to `False` and `EMAIL_USE_SSL` SHALL default to `True` (each overridable via environment; explicit env always wins). `EMAIL_USE_TLS` and `EMAIL_USE_SSL` SHALL NOT both be `True` (Django forbids it); for real SMTP the valid pairs are STARTTLS with port `587` (`EMAIL_USE_TLS=True`, `EMAIL_USE_SSL=False`) or implicit SSL with port `465` (`EMAIL_USE_TLS=False`, `EMAIL_USE_SSL=True`). The no-env defaults (`EMAIL_USE_TLS=False`, `EMAIL_USE_SSL=True`, `EMAIL_PORT=587`) are console-ignored in dev/test; production SHALL set explicitly paired host/port/flag values from the environment. Dev/test environments SHALL default to the console backend (no credentials needed); production SHALL use SMTP with credentials from the environment. `.env.dev.example` and `.env.prod.example` SHALL document all new variables including `EMAIL_USE_SSL` with the correct port pairing.

#### Scenario: Dev sends to console without credentials
- **WHEN** a cash email fires in the dev environment with no SMTP variables set
- **THEN** the email content SHALL be printed to the runserver console and no network call SHALL occur.

#### Scenario: Tests capture mail in outbox
- **WHEN** any test triggers a cash transition
- **THEN** the emails SHALL be captured via Django's `locmem` backend and assertable through `django.core.mail.outbox` with no extra test dependency.

#### Scenario: Defaults select implicit SSL without env
- **WHEN** settings are imported with no `EMAIL_USE_TLS` / `EMAIL_USE_SSL` / `EMAIL_PORT` overrides
- **THEN** `EMAIL_USE_TLS` SHALL be `False` and `EMAIL_USE_SSL` SHALL be `True`.

### Requirement: Central cash mailer service

The system SHALL provide `subscriptions/services/notifications.py` as the subscription-domain mailer, exposing `send_cash_pending(artist, actor)`, `send_cash_active(artist, actor)`, and `send_cash_canceled(artist, actor)`. Artwork-sale mail SHALL live in `artworks/sale_notifications.py` (see `sales-emails` delta); both mailers SHALL share best-effort and per-audience rendering via `core/mail_utils.py`. Each function SHALL send two separate `EmailMultiAlternatives` messages (TXT + HTML alternatives): an artist receipt (`to=[artist.email]`, artist body) and an admin notice (`to=EMAILS_NOTIFICATIONS`, subject prefixed `[Enredarte]`, naming the artist, dedicated operational body). Each function SHALL log a warning and skip the admin send when `EMAILS_NOTIFICATIONS` is empty. All subjects, bodies, and the `[Enredarte]` prefix SHALL be Spanish, consistent with the admin language.

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

#### Scenario: Cash senders originate from subscriptions module
- **WHEN** any `send_cash_*` sender runs
- **THEN** its implementation SHALL reside in `subscriptions/services/notifications.py`, and no sale sender SHALL reside there.

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

### Requirement: Triple-audience mailer for sales and online events

The system SHALL provide `send_sale_reserved / send_sale_paid / send_sale_delivery_complete / send_sale_shipped / send_sale_delivered / send_sale_cancelled / send_sale_refunded` from `artworks/sale_notifications.py` plus `send_online_canceling` and `send_online_canceled` from `subscriptions/services/notifications.py`, all Spanish, all `EmailMultiAlternatives` TXT+HTML. Sale senders SHALL address buyer (`order.buyer_email`), artist (`order.artwork.artist.email`, only for paid/delivery_complete/cancelled/refunded), and `EMAILS_NOTIFICATIONS` each as separate messages with per-audience subjects; the online senders SHALL address the artist + admin list. Any blank address or empty admin list SHALL skip just that audience with a `logger.warning` naming the kind and order/artist, exactly like the cash empty-list behavior. No existing cash sender's behavior SHALL change.

#### Scenario: Paid sender addresses three audiences
- **WHEN** `send_sale_paid(order)` runs with buyer, artist and two admin addresses configured
- **THEN** three messages SHALL be sent (buyer, artist, admin-list), each with TXT and HTML alternatives.

#### Scenario: Missing artist skips just the artist
- **WHEN** `send_sale_paid(order)` runs for an artwork whose artist has a blank email
- **THEN** buyer and admin mails SHALL still be sent and a warning SHALL be logged for the skipped artist send.

### Requirement: Per-audience template pairs for sales and online events

The system SHALL ship sale template pairs under `artworks/templates/artworks/email/` (`sale_reserved_{buyer,admin}`, `sale_paid_{buyer,artist,admin}`, `sale_delivery_complete_{buyer,artist,admin}`, `sale_shipped_{buyer,admin}`, `sale_delivered_{buyer,admin}`, `sale_cancelled_{buyer,artist,admin}`, `sale_refunded_{buyer,artist,admin}`, each `.txt` + `.html`, 36 files) and online pairs under `subscriptions/templates/subscriptions/email/` (`online_canceling` + `online_canceling_admin`, `online_canceled` + `online_canceled_admin`, each `.txt` + `.html`, 8 files), all following the cash convention (HTML primary, TXT fallback, shared context with `order`, `artwork`, `artist`, `buyer`, `host`, `admin_url`). Buyer/artist templates SHALL be Spanish with greeting (or order reference), what happened, what to do next, and a reply/contact line; admin templates SHALL be Spanish operational tone with buyer, artwork, artist, amount/currency, Stripe ids where relevant, acting actor where relevant, and the admin change-page link. The `online_canceling` pair SHALL state the artist stays visible until the paid period end; the `online_canceled` pair SHALL state the artist is no longer visible.

#### Scenario: Every new mail has both bodies
- **WHEN** any new sale or online sender runs
- **THEN** each sent message SHALL contain both `text/plain` and `text/html` alternatives rendering the same information.

### Requirement: Best-effort failure semantics for new senders
All new senders SHALL be best-effort: callers (buy view, summary view, delivery view, admin actions, cron/management commands, webhook handlers) SHALL catch send exceptions, log them, keep the already-persisted state change, and (for admin actions) show `messages.warning` instead of `messages.success`. Webhook callers SHALL register sends via `transaction.on_commit` so mail leaves only after commit and a mail failure SHALL NOT change the 200 response.

#### Scenario: SMTP outage during buy keeps sale
- **WHEN** reserved sends raise
- **THEN** the `201` SHALL still be returned with the `checkout_url` and the reservation SHALL persist.

### Requirement: Shared mail helpers owned by core

The system SHALL provide `core/mail_utils.py` exposing `send_best_effort(sender, *args, **kwargs)` and a per-audience renderer whose template base path is a **caller-supplied argument**, not a hardcoded namespace. `send_best_effort` SHALL swallow and log exceptions exactly as today. The renderer SHALL accept a full template base (e.g. `"artworks/email/sale_paid_buyer"` or `"subscriptions/email/online_canceling"`), render `f"{base}.txt"` and `f"{base}.html"` via `render_to_string`, attach the HTML alternative, send to recipients, and return `False` when recipients are empty. `artworks/sale_notifications.py` SHALL pass `artworks/email/sale_*` bases and `subscriptions/services/notifications.py` SHALL pass `subscriptions/email/*` bases; neither helper SHALL remain duplicated in a domain app, and no module SHALL rely on the renderer to prefix a fixed app namespace. Webhook, view, admin-action, and cron callers SHALL keep using `send_best_effort` so a mail failure never rolls back state or changes a webhook `200`.

#### Scenario: Sale mail renders from the artworks namespace

- **WHEN** `send_sale_paid(order)` renders its buyer, artist, and admin messages
- **THEN** the renderer SHALL resolve `artworks/email/sale_paid_{audience}.{txt,html}`, and no sale message SHALL require a `subscriptions/email/` template.

#### Scenario: Subscription mail still renders its own namespace

- **WHEN** `send_online_canceling(subscription)` renders artist and admin messages
- **THEN** the renderer SHALL resolve `subscriptions/email/online_canceling*` templates, unchanged from today.

#### Scenario: Sale and cash mailers share one implementation

- **WHEN** any sale or cash sender needs best-effort sending or per-audience rendering
- **THEN** it SHALL call `core.mail_utils.send_best_effort` / the shared renderer, with no local copy in `artworks` or `subscriptions`.

#### Scenario: Best-effort failure is swallowed and logged

- **WHEN** an underlying `msg.send()` raises inside `send_best_effort`
- **THEN** the exception SHALL be logged and SHALL NOT propagate to the caller.
