## MODIFIED Requirements

### Requirement: Sale-reserved emails to buyer and admin
The system SHALL send buyer + admin mails when `POST artworks/{slug}/buy/` creates a fresh reservation (`available → reserved`, new `pending_payment` order). The buyer mail (`to=[buyer_email]`) SHALL carry subject `"Tu compra está reservada / Your purchase is reserved"`, the live `checkout_url` + 30-minute expiry note, and SHALL provide both Spanish and English versions of the notification in the same template body (HTML and TXT alternatives), with Spanish first followed by an English section. The buyer body SHALL state, in both the Spanish and English sections, that the shown amount is the artwork price only with delivery cost agreed separately, and SHALL state that all works include a certificate of authenticity and secure delivery. The admin mail (`to=EMAILS_NOTIFICATIONS`, subject `"[Enredarte] Nueva reserva — {artwork} ({order})"`) SHALL carry buyer email, artwork title, amount/currency, Stripe session id, and the order admin link. Sends happen after the atomic block commits and SHALL be best-effort (failure never changes the `201`). Same-buyer reuse (`200` same URL) SHALL send nothing. The artist SHALL receive nothing on reserve.

#### Scenario: Fresh buy mails buyer and admin
- **WHEN** a buy creates a new `pending_payment` order with `checkout_url`
- **THEN** one buyer mail (with subject "Tu compra está reservada / Your purchase is reserved", checkout URL, Spanish and English copy) and one admin mail SHALL be sent, both TXT+HTML, and the response SHALL still be `201`.

#### Scenario: Reserved buyer body disambiguates price and states certificate
- **WHEN** the reserved buyer mail (TXT or HTML, Spanish or English section) is rendered
- **THEN** it SHALL contain the price-excludes-delivery note and the certificate + secure-delivery line alongside the artwork/amount block.

#### Scenario: Mail failure keeps the reservation
- **WHEN** SMTP raises during reserved sends
- **THEN** the order SHALL remain `pending_payment`, the artwork SHALL remain `reserved`, the failure SHALL be logged, and the response SHALL still be `201`.

#### Scenario: Same-buyer reuse sends nothing
- **WHEN** a buy reuses a live session (`200` existing `checkout_url`)
- **THEN** no reserved mail SHALL be sent.

### Requirement: Sale-paid emails to buyer, admin and artist
The system SHALL send buyer + admin + artist mails exactly once when an order truly transitions `pending_payment → paid_pending_data` (artwork → `sold`), from any firing path: `checkout.session.completed` (`payment_status == paid`), `async_payment_succeeded`, `OrderSummaryView` race fallback, lazy `reconcile_stale_reservations`, `sync_orders_from_stripe`. Each site SHALL send only when its transition call returns `True`. Subjects: buyer `"Tu pago fue confirmado / Payment confirmed"`, artist `"Tu obra {title} se vendió"`, admin `"[Enredarte] Venta pagada — {artwork} ({order})"`. Buyer body: bilingual receipt (amount/currency) in Spanish and English within the same template + delivery-form instructions + reply line, and SHALL state in both languages that the amount is the artwork price only with delivery cost agreed separately, plus that the work includes a certificate of authenticity and secure delivery coordinated by the team. Artist body: work title + amount + sold consequence + contact line. Admin body: buyer, artwork, artist, amount/currency, payment-intent id, admin link. Webhook paths SHALL send via `transaction.on_commit` and SHALL return 200 even if mail fails.

#### Scenario: Paid webhook mails all three once
- **WHEN** `checkout.session.completed` (paid) transitions an order
- **THEN** buyer (bilingual subject "Tu pago fue confirmado / Payment confirmed", bilingual Spanish and English body), artist and admin mails SHALL each be sent once with TXT+HTML alternatives.

#### Scenario: Paid buyer body disambiguates price and states certificate
- **WHEN** the paid buyer mail (TXT or HTML, Spanish or English section) is rendered
- **THEN** it SHALL contain the price-excludes-delivery note and the certificate + secure-delivery line alongside the artwork/amount block.

#### Scenario: Race paths do not double-mail
- **WHEN** the webhook already transitioned the order and the summary endpoint (or reconcile, or sync command) re-checks the same paid session
- **THEN** no additional paid mail SHALL be sent (transition returns `False`).

#### Scenario: Unpaid completed sends nothing
- **WHEN** `checkout.session.completed` arrives with `payment_status != "paid"`
- **THEN** no paid mail SHALL be sent and the order SHALL remain `pending_payment`.

### Requirement: Refunded emails to buyer, admin and artist
The system SHALL send buyer + admin + artist mails when the double-sale backstop marks an order `refunded` and issues the automatic Stripe refund (both webhook and reconcile paths, after `create_refund` succeeds). Subjects: buyer `"Tu reembolso está en camino / Your refund is on the way"`, artist `"Aviso de doble pago en {title}"`, admin `"[Enredarte] Reembolso por doble venta — {artwork} ({order})"`. Buyer body: bilingual notice in Spanish and English in the same template (apology + refund confirmation of full amount + timing note + reply line), and SHALL state in both languages that the refunded amount is the artwork price only with delivery cost agreed separately. Artist body: conflict explanation (work already sold, second payment refunded, no action needed). Admin body: both order slugs, payment-intent id, refund id, admin links. If `create_refund` raises, NO refunded mail SHALL be sent (handler raises → 500 → Stripe retry).

#### Scenario: Double-sale refunds and mails all three
- **WHEN** a paid session completes for an already-sold artwork and the refund succeeds
- **THEN** the order SHALL be `refunded` and buyer (bilingual subject "Tu reembolso está en camino / Your refund is on the way", bilingual body), artist and admin mails SHALL be sent.

#### Scenario: Refunded buyer body disambiguates price
- **WHEN** the refunded buyer mail (TXT or HTML, Spanish or English section) is rendered
- **THEN** it SHALL contain the price-excludes-delivery note alongside the refunded-amount block, and SHALL NOT promise a certificate.

#### Scenario: Refund failure sends nothing and retries
- **WHEN** the Stripe refund call raises
- **THEN** no refunded mail SHALL be sent, the error SHALL be logged, and the endpoint SHALL return 500.
