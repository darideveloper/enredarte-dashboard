## ADDED Requirements

### Requirement: Online cancellation-request emails to artist and admin

The system SHALL send Spanish artist + admin mails when an online (`payment_method="online"`) subscription **transitions into** the `canceling` state (Stripe `customer.subscription.updated` with `cancel_at_period_end=true`), where the artist SHALL remain visible through the paid period end. The mail SHALL be **transition-gated**: it SHALL send only when the previous stored status was not already `canceling`, so a repeat `subscription.updated` event (renewal, payment-method change) on an already-canceling subscription SHALL NOT re-mail. The artist mail (`to=[artist.email]`) SHALL carry subject `"Tu suscripción en línea será cancelada"` with a body containing: greeting naming the artist, one-line explanation (cancellation requested), the visibility consequence (profile stays visible until the paid period ends on `current_period_end`), and a reply/contact line. The admin mail (`to=EMAILS_NOTIFICATIONS`, subject `"[Enredarte] Suscripción en línea en cancelación — {artista}"`) SHALL carry artist name + email, the transition with its visibility consequence, the Stripe customer/subscription ids, and the artist admin change-page link. Cash rows SHALL be ignored (existing cash guard) and SHALL send nothing. Sends SHALL run via `transaction.on_commit`, be best-effort (mail failure keeps the state, logs, returns 200), and fire at most once per `event_id` (existing `StripeEvent` idempotency). A `canceling` event SHALL NOT trigger the final-`canceled` mail.

#### Scenario: Cancel-request mails artist and admin, artist stays visible
- **WHEN** `customer.subscription.updated` derives a `canceling` status for an online subscription that was not previously `canceling`
- **THEN** the subscription SHALL become `canceling`, the artist SHALL remain visible, and artist + admin mails (TXT+HTML) SHALL each be sent once with the "visible until period end" copy.

#### Scenario: Cash row ignored
- **WHEN** the event correlates to a `payment_method="cash"` row
- **THEN** state SHALL be unchanged and no online-canceling mail SHALL be sent.

#### Scenario: Repeat update of an already-canceling sub does not re-mail
- **WHEN** `customer.subscription.updated` arrives for a subscription already `canceling` (e.g. a renewal or payment-method update)
- **THEN** the status SHALL remain `canceling` and SHALL NOT send a second `online_canceling` mail.

### Requirement: Online cancellation-final emails to artist and admin

The system SHALL send Spanish artist + admin mails when an online subscription reaches the terminal `canceled` state (Stripe `customer.subscription.deleted`), where the artist SHALL be hidden via `compute_is_active`. The artist mail (`to=[artist.email]`) SHALL carry subject `"Tu suscripción en línea fue cancelada"` with a body containing: greeting naming the artist, one-line explanation (subscription ended), the visibility consequence (profile no longer visible), and a reply/contact line. The admin mail (`to=EMAILS_NOTIFICATIONS`, subject `"[Enredarte] Suscripción en línea cancelada — {artista}"`) SHALL carry artist name + email, the transition with its visibility consequence, the Stripe customer/subscription ids, and the artist admin change-page link. Cash rows SHALL be ignored (existing cash guard) and SHALL send nothing. Sends SHALL run via `transaction.on_commit`, be best-effort (mail failure keeps the cancelled state, logs, returns 200), and fire at most once per `event_id`. A `canceled` event SHALL NOT re-trigger the `canceling` mail. If the `canceled` event arrives without a prior `canceling` observation, SHALL it still mail the final notice (no `canceling` mail is sent retroactively).

#### Scenario: Online delete mails artist and admin
- **WHEN** `customer.subscription.deleted` derives a `canceled` status for an online subscription
- **THEN** the subscription SHALL become `canceled`, the artist SHALL be hidden, and artist + admin mails (TXT+HTML) SHALL each be sent once with the "no longer visible" copy.

#### Scenario: Cash row ignored
- **WHEN** `customer.subscription.deleted` correlates to a `payment_method="cash"` row
- **THEN** state SHALL be unchanged and no online-canceled mail SHALL be sent.

#### Scenario: Duplicate delivery sends nothing new
- **WHEN** the same `event_id` is delivered twice
- **THEN** the second delivery SHALL return 200 with no state change and no additional mail.

#### Scenario: Mail failure keeps cancellation
- **WHEN** SMTP raises during online-canceled sends
- **THEN** the cancelled state SHALL persist, the failure SHALL be logged, and the endpoint SHALL still return 200.