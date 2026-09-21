# sales-emails Specification

## Purpose
Transactional emails that notify the buyer, the artist and the admin list at each stage of an artwork sale lifecycle: reserved, paid, delivery complete, shipped, delivered, cancelled and refunded. Each sale sender is best-effort and per-audience, extending the shared `EMAILS_NOTIFICATIONS` infrastructure with no change to existing cash senders.
## Requirements
### Requirement: Sale-reserved emails to buyer and admin
The system SHALL send Spanish buyer + admin mails when `POST artworks/{slug}/buy/` creates a fresh reservation (`available → reserved`, new `pending_payment` order). The buyer mail (`to=[buyer_email]`) SHALL carry subject `"Tu compra está reservada: completa tu pago"` and the live `checkout_url` + 30-minute expiry note. The admin mail (`to=EMAILS_NOTIFICATIONS`, subject `"[Enredarte] Nueva reserva — {artwork} ({order})"`) SHALL carry buyer email, artwork title, amount/currency, Stripe session id, and the order admin link. Sends happen after the atomic block commits and SHALL be best-effort (failure never changes the `201`). Same-buyer reuse (`200` same URL) SHALL send nothing. The artist SHALL receive nothing on reserve.

#### Scenario: Fresh buy mails buyer and admin
- **WHEN** a buy creates a new `pending_payment` order with `checkout_url`
- **THEN** one buyer mail (with the checkout URL) and one admin mail SHALL be sent, both TXT+HTML, and the response SHALL still be `201`.

#### Scenario: Mail failure keeps the reservation
- **WHEN** SMTP raises during reserved sends
- **THEN** the order SHALL remain `pending_payment`, the artwork SHALL remain `reserved`, the failure SHALL be logged, and the response SHALL still be `201`.

#### Scenario: Same-buyer reuse sends nothing
- **WHEN** a buy reuses a live session (`200` existing `checkout_url`)
- **THEN** no reserved mail SHALL be sent.

### Requirement: Sale-paid emails to buyer, admin and artist
The system SHALL send Spanish buyer + admin + artist mails exactly once when an order truly transitions `pending_payment → paid_pending_data` (artwork → `sold`), from any firing path: `checkout.session.completed` (`payment_status == paid`), `async_payment_succeeded`, `OrderSummaryView` race fallback, lazy `reconcile_stale_reservations`, `sync_orders_from_stripe`. Each site SHALL send only when its transition call returns `True`. Subjects: buyer `"Tu pago fue confirmado"`, artist `"Tu obra {title} se vendió"`, admin `"[Enredarte] Venta pagada — {artwork} ({order})"`. Buyer body: receipt (amount/currency) + delivery-form link + reply line. Artist body: work title + amount + sold consequence + contact line. Admin body: buyer, artwork, artist, amount/currency, payment-intent id, admin link. Webhook paths SHALL send via `transaction.on_commit` and SHALL return 200 even if mail fails.

#### Scenario: Paid webhook mails all three once
- **WHEN** `checkout.session.completed` (paid) transitions an order
- **THEN** buyer, artist and admin mails SHALL each be sent once with TXT+HTML alternatives.

#### Scenario: Race paths do not double-mail
- **WHEN** the webhook already transitioned the order and the summary endpoint (or reconcile, or sync command) re-checks the same paid session
- **THEN** no additional paid mail SHALL be sent (transition returns `False`).

#### Scenario: Unpaid completed sends nothing
- **WHEN** `checkout.session.completed` arrives with `payment_status != "paid"`
- **THEN** no paid mail SHALL be sent and the order SHALL remain `pending_payment`.

### Requirement: Delivery-complete emails to buyer, admin and artist
The system SHALL send Spanish buyer + admin + artist mails when `POST orders/{slug}/delivery/` transitions `paid_pending_data → data_complete`. Subjects: buyer `"Recibimos tus datos de entrega"`, artist `"Datos de entrega listos para {title}"`, admin `"[Enredarte] Datos de entrega — {artwork} ({order})"`. The admin body SHALL include the full delivery address + buyer contact + admin link. The artist body SHALL state the address-sharing purpose explicitly ("para coordinar la entrega") and SHALL NOT include Stripe payment ids. Non-transition calls (`409`, `400`) SHALL send nothing.

#### Scenario: Delivery submit mails all three
- **WHEN** a valid delivery form completes the transition
- **THEN** buyer, artist and admin mails SHALL be sent and the order SHALL be `data_complete`.

#### Scenario: Duplicate submit sends nothing new
- **WHEN** delivery is posted for an order already past `paid_pending_data`
- **THEN** the response SHALL be `409` and no delivery mail SHALL be sent.

### Requirement: Shipped emails to buyer and admin
The system SHALL send Spanish buyer + admin mails when the `Marcar enviada` admin action transitions `data_complete → shipped`. Subjects: buyer `"Tu obra va en camino"`, admin `"[Enredarte] Pedido enviado — {artwork} ({order})"`. Buyer body: shipped confirmation + what to expect + reply line. Admin body: order state + admin link. The artist SHALL receive nothing. Invalid transitions SHALL send nothing. Mail failure SHALL keep the shipped state with the existing warning message.

#### Scenario: Mark shipped mails buyer and admin
- **WHEN** `marcar_enviada` transitions an order
- **THEN** buyer and admin mails SHALL be sent and the order SHALL be `shipped`.

#### Scenario: Invalid ship transition sends nothing
- **WHEN** `marcar_enviada` is attempted on a non-`data_complete` order
- **THEN** state SHALL be unchanged and no mail SHALL be sent.

### Requirement: Delivered emails to buyer and admin
The system SHALL send Spanish buyer + admin mails when the `Marcar entregada` admin action transitions `shipped → delivered`. Subjects: buyer `"Tu obra fue entregada ¡gracias por tu compra!"`, admin `"[Enredarte] Pedido entregado — {artwork} ({order})"`. Buyer body: thank-you + care/contact line. Admin body: closed-state confirmation + admin link. The artist SHALL receive nothing. Invalid transitions SHALL send nothing.

#### Scenario: Mark delivered mails buyer and admin
- **WHEN** `marcar_entregada` transitions an order
- **THEN** buyer and admin mails SHALL be sent and the order SHALL be `delivered`.

### Requirement: Cancelled emails to buyer, admin and artist
The system SHALL send Spanish buyer + admin + artist mails exactly once when an order truly transitions `pending_payment → cancelled` (artwork → `available`), from any path: `checkout.session.expired`, `async_payment_failed`, `release_expired_orders`, `sync_orders_from_stripe`, manual `Liberar reserva`, lazy reconcile. Each site SHALL send only when `cancel_order` returns `True`. Subjects: buyer `"Tu pago no se completó"`, artist `"La reserva de {title} se liberó"`, admin `"[Enredarte] Reserva cancelada — {artwork} ({order})"`. Buyer body: what happened + re-try note (check artwork availability) + reply line. Artist body: hold released, work is available again. Admin body: reason (expired/failed/manual/reaper) + buyer + admin link. Webhook paths via `on_commit`, best-effort.

#### Scenario: Expiry mails all three once
- **WHEN** `checkout.session.expired` cancels a pending order
- **THEN** buyer, artist and admin mails SHALL each be sent once.

#### Scenario: Cancel after terminal state sends nothing
- **WHEN** an expiry event arrives for an order already past `pending_payment`
- **THEN** state SHALL be unchanged and no mail SHALL be sent.

### Requirement: Refunded emails to buyer, admin and artist
The system SHALL send Spanish buyer + admin + artist mails when the double-sale backstop marks an order `refunded` and issues the automatic Stripe refund (both webhook and reconcile paths, after `create_refund` succeeds). Subjects: buyer `"Tu reembolso está en camino"`, artist `"Aviso de doble pago en {title}"`, admin `"[Enredarte] Reembolso por doble venta — {artwork} ({order})"`. Buyer body: apology + refund confirmation (full amount, timing via Stripe) + reply line. Artist body: conflict explanation (work already sold, second payment refunded, no action needed). Admin body: both order slugs, payment-intent id, refund id, admin links. If `create_refund` raises, NO refunded mail SHALL be sent (handler raises → 500 → Stripe retry).

#### Scenario: Double-sale refunds and mails all three
- **WHEN** a paid session completes for an already-sold artwork and the refund succeeds
- **THEN** the order SHALL be `refunded` and buyer, artist and admin mails SHALL be sent.

#### Scenario: Refund failure sends nothing and retries
- **WHEN** the Stripe refund call raises
- **THEN** no refunded mail SHALL be sent, the error SHALL be logged, and the endpoint SHALL return 500.