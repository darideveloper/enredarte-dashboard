## MODIFIED Requirements

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

## MODIFIED Requirements

### Requirement: Cash rows carry no Stripe identifiers
Cash rows SHALL NOT require or populate `stripe_customer_id` / `stripe_subscription_id` (both stay empty); `signup_url` stays empty so the "Copiar link" button never renders for cash. `raw_state` on cash transitions SHALL store a small audit dict (`{"cash": true, ...}`) instead of a Stripe object. When a row is converted to cash from a never-billing online row, the previously stored `stripe_customer_id` / `stripe_subscription_id` SHALL be cleared as part of the conversion.

#### Scenario: Cash row has no Stripe linkage
- **WHEN** any cash transition completes
- **THEN** `stripe_customer_id` and `stripe_subscription_id` SHALL remain empty and `signup_url` SHALL remain empty.

#### Scenario: Converting an online link row clears Stripe identifiers
- **WHEN** an online `pending` row that previously generated a link (with `stripe_customer_id` set) is marked as cash
- **THEN** `stripe_customer_id` and `stripe_subscription_id` SHALL be cleared to empty on the resulting cash row.