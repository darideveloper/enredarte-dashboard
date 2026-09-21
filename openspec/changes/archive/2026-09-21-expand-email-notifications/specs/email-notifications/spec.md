## ADDED Requirements

### Requirement: Triple-audience mailer for sales and online events

The system SHALL extend `subscriptions/services/notifications.py` (still the only module that sends mail) with `send_sale_reserved / send_sale_paid / send_sale_delivery_complete / send_sale_shipped / send_sale_delivered / send_sale_cancelled / send_sale_refunded` plus `send_online_canceling` and `send_online_canceled`, all Spanish, all `EmailMultiAlternatives` TXT+HTML. Sale senders SHALL address buyer (`order.buyer_email`), artist (`order.artwork.artist.email`, only for paid/delivery_complete/cancelled/refunded), and `EMAILS_NOTIFICATIONS` each as separate messages with per-audience subjects; the online senders SHALL address the artist + admin list. Any blank address or empty admin list SHALL skip just that audience with a `logger.warning` naming the kind and order/artist, exactly like the cash empty-list behavior. No existing cash sender's behavior SHALL change.

#### Scenario: Paid sender addresses three audiences
- **WHEN** `send_sale_paid(order)` runs with buyer, artist and two admin addresses configured
- **THEN** three messages SHALL be sent (buyer, artist, admin-list), each with TXT and HTML alternatives.

#### Scenario: Missing artist skips just the artist
- **WHEN** `send_sale_paid(order)` runs for an artwork whose artist has a blank email
- **THEN** buyer and admin mails SHALL still be sent and a warning SHALL be logged for the skipped artist send.

### Requirement: Per-audience template pairs for sales and online events

The system SHALL ship template pairs under `subscriptions/templates/subscriptions/email/` following the cash convention (HTML primary, TXT fallback, shared context with `order`, `artwork`, `artist`, `buyer`, `host`, `admin_url`): `sale_reserved_{buyer,admin}`, `sale_paid_{buyer,artist,admin}`, `sale_delivery_complete_{buyer,artist,admin}`, `sale_shipped_{buyer,admin}`, `sale_delivered_{buyer,admin}`, `sale_cancelled_{buyer,artist,admin}`, `sale_refunded_{buyer,artist,admin}`, plus `online_canceling` + `online_canceling_admin` and `online_canceled` + `online_canceled_admin` (each `.txt` + `.html`, 44 files). Buyer/artist templates SHALL be Spanish with greeting (or order reference), what happened, what to do next, and a reply/contact line; admin templates SHALL be Spanish operational tone with buyer, artwork, artist, amount/currency, Stripe ids where relevant, acting actor where relevant, and the admin change-page link. The `online_canceling` pair SHALL state the artist stays visible until the paid period end; the `online_canceled` pair SHALL state the artist is no longer visible.

#### Scenario: Every new mail has both bodies
- **WHEN** any new sale or online sender runs
- **THEN** each sent message SHALL contain both `text/plain` and `text/html` alternatives rendering the same information.

### Requirement: Best-effort failure semantics for new senders

All new senders SHALL be best-effort: callers (buy view, summary view, delivery view, admin actions, cron/management commands, webhook handlers) SHALL catch send exceptions, log them, keep the already-persisted state change, and (for admin actions) show `messages.warning` instead of `messages.success`. Webhook callers SHALL register sends via `transaction.on_commit` so mail leaves only after commit and a mail failure SHALL NOT change the 200 response.

#### Scenario: SMTP outage during buy keeps sale
- **WHEN** reserved sends raise
- **THEN** the `201` SHALL still be returned with the `checkout_url` and the reservation SHALL persist.
