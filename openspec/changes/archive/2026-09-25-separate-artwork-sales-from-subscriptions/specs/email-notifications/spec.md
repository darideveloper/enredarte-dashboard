## ADDED Requirements

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

## MODIFIED Requirements

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
