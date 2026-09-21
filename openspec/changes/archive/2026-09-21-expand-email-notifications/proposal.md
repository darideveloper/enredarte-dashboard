## Why

Artwork sales and online (Stripe) subscriptions complete money movements in silence: buyers get no receipt, artists learn their work sold only by checking the admin, operators learn about sales only by polling, and online cancellations vanish without a trace. Cash subscriptions already mail artist + admin on every transition — sales and online flows should meet the same bar now that checkout is live.

## What Changes

- Extend `subscriptions/services/notifications.py` (Approach A, single mailer module) with 9 new senders: `send_sale_reserved / paid / delivery_complete / shipped / delivered / cancelled / refunded` + `send_online_canceling` + `send_online_canceled`, each sending per-audience `EmailMultiAlternatives` TXT+HTML (buyer and/or artist receipt + admin notice), Spanish-only, best-effort (never rolls back state, never turns a webhook 200 into a 500).
- Fire sale mails at their owning transitions: `buy` (reserved), paid-transition sites (webhook `completed` / async-succeeded / summary-race / reconcile / sync command — only when the transition actually fires), delivery submit, admin `Marcar enviada / entregada`, expiry/failure paths (`expired` webhook, async-failed, reaper, manual `Liberar reserva`), double-sale refund backstop.
- Fire online-cancellation mails from both Stripe subscription phases (operator decision): `subscription.updated` → `CANCELING` (artist still visible until period end) fires `send_online_canceling`, and `subscription.deleted` → `CANCELED` (hidden) fires `send_online_canceled`, idempotent per `StripeEvent` and transition-gated so repeat `subscription.updated` events for an already-`canceling` sub do not re-mail.
- Ship per-audience template pairs following the existing `cash_{kind}[_admin].{txt,html}` convention (buyer/artist/admin variants), sharing one context (`order`, `artwork`, `artist`, `buyer`, `host`, `admin_url`, `checkout_url` where live).
- Audience matrix per explore decision: reserved/shipped/delivered = buyer+admin; paid/delivery-complete/cancelled/refunded = buyer+admin+artist; online cancellation = artist+admin (at both `canceling` and `canceled`). Skip-and-log when an address is missing (no artist email, empty `EMAILS_NOTIFICATIONS`).

## Capabilities

### New Capabilities

- `sales-emails`: the 7 artwork-sale triggers, audiences, subjects, template contents, firing points, idempotency (paid only on real transition), and best-effort failure semantics.
- `subscription-emails`: the two-phase online cancellation triggers (Stripe `customer.subscription.updated` → `canceling`, `customer.subscription.deleted` → `canceled`), artist+admin audiences, subjects, templates, webhook firing points, idempotency via `StripeEvent`, best-effort semantics.

### Modified Capabilities

- `email-notifications`: central mailer grows from cash-only dual-send (artist+admin) to triple-audience (buyer/artist/admin) with 9 new senders; template convention extended to `sale_*` / `online_{canceling,canceled}` per-audience pairs; empty-recipient skip-and-log now covers buyer/artist addresses as well as the admin list.

## Impact

- Code: `subscriptions/services/notifications.py` (new senders + generic triple-send helper), 7 sale firing points (`artworks/views.py` buy/summary/delivery, `artworks/services.py` transitions, `subscriptions/webhooks.py` artwork handlers, `release_expired_orders` + `sync_orders_from_stripe` commands, `artworks/admin.py` shipment/release actions), 1 online firing point (`subscriptions/webhooks.py` subscription-deleted), 44 new templates (22 names × `.txt`+`.html`) under `subscriptions/templates/subscriptions/email/`.
- Systems: SMTP volume rises (notably reserved+cancelled pairs on abandoned checkouts); no new env vars, no new endpoints, no API contract changes (mails carry `checkout_url`/slugs already returned by the API); online cancellation emits two mails (canceling + canceled) per determined phase.
- Risk: reserved/cancelled noise on abandoned holds; paid double-fire from webhook-vs-summary race (guarded by transition-return check); buyer address shared with artist on delivery-complete (intentional per operator decision, template states the reason); online cancel is two-phase so both `canceling` and `canceled` momentarily fire close together.
