# cash-payments Specification

## Purpose
Manual cash subscription lifecycle for artists who pay outside Stripe, operated fully from the Artist admin with Spanish operator messages and email notifications on every transition.
## Requirements
### Requirement: Cash payment method discriminator
The system SHALL provide an `ArtistSubscription.payment_method` field with choices `online` (default) and `cash`, with `verbose_name`/`help_text` per project model conventions. All existing rows SHALL read as `online` after migration (field default, no data rewrite). Cash rows SHALL reuse the existing `Status` values (`pending`/`active`/`canceled`) and the existing `compute_is_active()` derivation without modification.

#### Scenario: New subscription defaults to online
- **WHEN** an `ArtistSubscription` is created through any existing flow (link generation, webhook upsert)
- **THEN** `payment_method` SHALL be `"online"` unless explicitly set to `"cash"`.

#### Scenario: Cash reuses status and visibility derivation
- **WHEN** a cash row holds `status="pending"`, `"active"`, or `"canceled"`
- **THEN** `compute_is_active()` SHALL return `False`, `True`, `False` respectively — identical to the online meanings, with no code change to the derivation function.

### Requirement: Mark artist as cash (pending)
The system SHALL provide a "Marcar como efectivo" changeform action on the Artist admin change page that registers a cash subscription. The action SHALL be visible only when no live subscription is billing: no subscription row, a cash-`canceled` row, or an online row that is not actively billing — i.e. status `pending`, `canceled`, `canceling`, or `active` with `cancel_at_period_end=True`. The action SHALL be hidden, and direct URL execution refused at the Unfold permission boundary (403) with no mutation and no email, when the online row is actively billing — i.e. status `active` (without a cancel request) or `past_due`; direct execution for those SHALL also hit the defensive `messages.error("Este artista tiene una suscripción en línea activa. Cancélala en Stripe antes de marcarlo como efectivo.")` guard. On execution it SHALL set `payment_method="cash"`, `status="pending"`, clear `signup_url`/`signup_url_expires_at` AND `stripe_customer_id`/`stripe_subscription_id`, persist `is_active=False` via `compute_is_active`, stamp `last_synced_at`, and fire the pending cash emails. On success it SHALL show `messages.success("Artista registrado para pago en efectivo. Pendiente de confirmación.")`. When the artist has no email the button IS reachable, so execution SHALL refuse with `messages.error("Este artista no tiene un correo electrónico. Captura uno antes de marcarlo como efectivo.")` + 302 and no mutation. All operator-visible messages SHALL be Spanish.

#### Scenario: Mark cash for artist without subscription
- **WHEN** an operator clicks "Marcar como efectivo" for an artist with an email and no subscription row
- **THEN** the system SHALL create `ArtistSubscription(payment_method="cash", status="pending")`, set `Artist.is_active=False`, show "Artista registrado para pago en efectivo. Pendiente de confirmación.", and send the pending emails to the artist and the admin list.

#### Scenario: Mark cash for online pending row with a generated link
- **WHEN** an operator clicks "Marcar como efectivo" for an artist whose online row is `pending` with a generated `signup_url` and `stripe_customer_id` (link never paid)
- **THEN** the action SHALL be visible, and on execution SHALL clear `signup_url`, `signup_url_expires_at`, `stripe_customer_id`, and `stripe_subscription_id`, set `payment_method="cash"`/`status="pending"`, show "Artista registrado para pago en efectivo. Pendiente de confirmación.", and send the pending emails.

#### Scenario: Mark cash for active row with cancel requested
- **WHEN** an operator clicks "Marcar como efectivo" for an artist whose online row is `active` with `cancel_at_period_end=True`
- **THEN** the action SHALL be visible and SHALL convert the row to cash as above.

#### Scenario: Mark cash for canceling online row
- **WHEN** an operator clicks "Marcar como efectivo" for an artist whose online row is `canceling` (paid through period end, not yet fully canceled)
- **THEN** the action SHALL be visible and SHALL convert the row to cash as above.

#### Scenario: Mark cash refused with active online subscription
- **WHEN** an operator executes the "Marcar como efectivo" URL directly for an artist with an online `active` (not cancel-requested) subscription (button hidden)
- **THEN** the system SHALL refuse with 403, SHALL NOT mutate the row, and SHALL NOT send any email.

#### Scenario: Mark cash refused for past_due online row
- **WHEN** an operator executes the "Marcar como efectivo" URL directly for an artist with an online `past_due` subscription
- **THEN** the system SHALL refuse with 403, SHALL NOT mutate the row, and SHALL NOT send any email.

#### Scenario: Mark cash refused without artist email
- **WHEN** an operator clicks "Marcar como efectivo" for an artist with an empty email
- **THEN** the system SHALL show "Este artista no tiene un correo electrónico. Captura uno antes de marcarlo como efectivo." and redirect without creating a subscription (same pattern as link generation without email).

### Requirement: Confirm cash payment (active, indefinite)
The system SHALL provide a "Confirmar pago" changeform action, visible for cash rows with `status="pending"`, `"active"`, or `"past_due"`. On execution it SHALL set `status="active"`, stamp `cash_last_paid_at = today`, set `current_period_end` to end-of-day (23:59 project timezone) on `max(today, current renew date-part) + 1 calendar month` (same-day-next-month, month-end clamped; initializing both dates when renew is null), persist `is_active=True` via `compute_is_active`, stamp `last_synced_at`, record `{"cash": true, "confirmed_by": <username>}` provenance in `raw_state`, fire the active cash emails, and show `messages.success("Pago en efectivo confirmado. El artista ya es visible.")`. Each execution counts as one monthly payment: re-confirming an `active` row extends the renew date and re-sends the receipt (no duplicate suppression). Direct URL execution for non-eligible rows is refused at the permission boundary (403). All operator-visible messages SHALL be Spanish.

#### Scenario: Confirm cash payment makes artist visible indefinitely
- **WHEN** an operator clicks "Confirmar pago" for a cash-`pending` artist
- **THEN** `status` SHALL become `"active"`, `Artist.is_active` SHALL become `True`, the artist SHALL appear in `GET /api/artworks/artists/`, `cash_last_paid_at` SHALL be today, `current_period_end` SHALL be end-of-day one calendar month out, the message SHALL be "Pago en efectivo confirmado. El artista ya es visible.", and the active emails SHALL be sent.

#### Scenario: Re-confirm during grace recovers to active
- **WHEN** an operator clicks "Confirmar pago" for a cash-`past_due` artist inside the grace window
- **THEN** `status` SHALL return to `"active"`, the renew date SHALL extend one month, and the receipt SHALL be sent again.

#### Scenario: Double confirm extends instead of no-op
- **WHEN** an operator clicks "Confirmar pago" for an already cash-`active` artist
- **THEN** the renew date SHALL extend one further month and the receipt SHALL be sent (each click = one payment). The old no-op behavior is removed.

### Requirement: Cancel cash subscription
The system SHALL provide a "Cancelar efectivo" changeform action, visible for cash rows with `status="pending"`, `"active"`, or `"past_due"`. On execution it SHALL set `status="canceled"`, persist `is_active=False` via `compute_is_active`, stamp `last_synced_at`, fire the canceled cash emails, and show `messages.success("Suscripción en efectivo cancelada. El artista ya no es visible.")`. After cancellation the artist MAY return to the online flow ("Generar link" reappears); re-entering the online flow SHALL reset the row to `payment_method="online"` / `status="pending"` (clearing the cash audit and `cash_last_paid_at`) so Stripe webhooks track it again — hybrid cash+Stripe rows SHALL NOT persist. The artist MAY also be re-marked as cash (which clears both dates for a fresh cycle). All operator-visible messages SHALL be Spanish.

#### Scenario: Cancel active cash hides artist
- **WHEN** an operator clicks "Cancelar efectivo" for a cash-`active` artist
- **THEN** `status` SHALL become `"canceled"`, `Artist.is_active` SHALL become `False`, the artist SHALL disappear from the public API, the message SHALL be "Suscripción en efectivo cancelada. El artista ya no es visible.", and the canceled emails SHALL be sent.

#### Scenario: Cancel during grace hides immediately
- **WHEN** an operator clicks "Cancelar efectivo" for a cash-`past_due` artist
- **THEN** `status` SHALL become `"canceled"` at once (no waiting for grace end) with the same message and emails.

#### Scenario: Cash actions hidden for online rows
- **WHEN** an administrator opens an Artist change form whose subscription is `payment_method="online"` with any link or Stripe identifiers
- **THEN** none of "Marcar como efectivo", "Confirmar pago", "Cancelar efectivo" SHALL be shown.

### Requirement: Cash rows carry no Stripe identifiers
Cash rows SHALL NOT require or populate `stripe_customer_id` / `stripe_subscription_id` (both stay empty); `signup_url` stays empty so the "Copiar link" button never renders for cash. `raw_state` on cash transitions SHALL store a small audit dict (`{"cash": true, ...}`) instead of a Stripe object. When a row is converted to cash from a never-billing online row, the previously stored `stripe_customer_id` / `stripe_subscription_id` SHALL be cleared as part of the conversion.

#### Scenario: Cash row has no Stripe linkage
- **WHEN** any cash transition completes
- **THEN** `stripe_customer_id` and `stripe_subscription_id` SHALL remain empty and `signup_url` SHALL remain empty.

#### Scenario: Converting an online link row clears Stripe identifiers
- **WHEN** an online `pending` row that previously generated a link (with `stripe_customer_id` set) is marked as cash
- **THEN** `stripe_customer_id` and `stripe_subscription_id` SHALL be cleared to empty on the resulting cash row.

