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
The system SHALL provide a "Marcar como efectivo" changeform action on the Artist admin change page that registers a cash subscription. The action SHALL be visible only when no active payment path exists (no subscription row, a cash-`canceled` row, or an online row that never started: no `signup_url` and no `stripe_customer_id`). On execution it SHALL set `payment_method="cash"`, `status="pending"`, clear any `signup_url`/`signup_url_expires_at`, persist `is_active=False` via `compute_is_active`, stamp `last_synced_at`, and fire the pending cash emails. On success it SHALL show `messages.success("Artista registrado para pago en efectivo. Pendiente de confirmación.")`. When an online `pending`/`active`/`past_due`/`canceling` row or a cash `pending`/`active` row already exists, the button is hidden and direct URL execution is refused at the Unfold permission boundary (403) with no mutation and no email; the method additionally keeps a defensive `messages.error("Este artista tiene una suscripción en línea activa. Cancélala en Stripe antes de marcarlo como efectivo.")` guard. When the artist has no email the button IS reachable, so execution SHALL refuse with `messages.error("Este artista no tiene un correo electrónico. Captura uno antes de marcarlo como efectivo.")` + 302 and no mutation. All operator-visible messages SHALL be Spanish.

#### Scenario: Mark cash for artist without subscription
- **WHEN** an operator clicks "Marcar como efectivo" for an artist with an email and no subscription row
- **THEN** the system SHALL create `ArtistSubscription(payment_method="cash", status="pending")`, set `Artist.is_active=False`, show "Artista registrado para pago en efectivo. Pendiente de confirmación.", and send the pending emails to the artist and the admin list.

#### Scenario: Mark cash refused with active online subscription
- **WHEN** an operator executes the "Marcar como efectivo" URL directly for an artist with an online `active` subscription (button hidden)
- **THEN** the system SHALL refuse with 403, SHALL NOT mutate the row, and SHALL NOT send any email.

#### Scenario: Mark cash refused without artist email
- **WHEN** an operator clicks "Marcar como efectivo" for an artist with an empty email
- **THEN** the system SHALL show "Este artista no tiene un correo electrónico. Captura uno antes de marcarlo como efectivo." and redirect without creating a subscription (same pattern as link generation without email).

### Requirement: Confirm cash payment (active, indefinite)
The system SHALL provide a "Confirmar pago" changeform action, visible only for cash rows with `status="pending"`. On execution it SHALL set `status="active"`, persist `is_active=True` via `compute_is_active`, stamp `last_synced_at`, record `{"cash": true, "confirmed_by": <username>}` provenance in `raw_state`, fire the active cash emails, and show `messages.success("Pago en efectivo confirmado. El artista ya es visible.")`. Re-confirming an already-`active` cash row is structurally impossible via the UI (button hidden) and direct URL execution is refused at the permission boundary (403) with no mutation and no duplicate email; the method additionally keeps a defensive informational guard ("El pago en efectivo ya estaba confirmado."). Cash `active` has no expiry: no `current_period_end` is required and no background job ever flips it — only "Cancelar efectivo" ends it. All operator-visible messages SHALL be Spanish.

#### Scenario: Confirm cash payment makes artist visible indefinitely
- **WHEN** an operator clicks "Confirmar pago" for a cash-`pending` artist
- **THEN** `status` SHALL become `"active"`, `Artist.is_active` SHALL become `True`, the artist SHALL appear in `GET /api/artworks/artists/`, the message SHALL be "Pago en efectivo confirmado. El artista ya es visible.", and the active emails SHALL be sent.

#### Scenario: Double confirm sends no duplicate email
- **WHEN** an operator executes the "Confirmar pago" URL directly for an already cash-`active` artist (button hidden)
- **THEN** the system SHALL refuse with 403, SHALL NOT change the row, and SHALL NOT send any email.

### Requirement: Cancel cash subscription
The system SHALL provide a "Cancelar efectivo" changeform action, visible only for cash rows with `status="pending"` or `"active"`. On execution it SHALL set `status="canceled"`, persist `is_active=False` via `compute_is_active`, stamp `last_synced_at`, fire the canceled cash emails, and show `messages.success("Suscripción en efectivo cancelada. El artista ya no es visible.")`. After cancellation the artist MAY return to the online flow ("Generar link" reappears); re-entering the online flow SHALL reset the row to `payment_method="online"` / `status="pending"` (clearing the cash audit) so Stripe webhooks track it again — hybrid cash+Stripe rows SHALL NOT persist. The artist MAY also be re-marked as cash. All operator-visible messages SHALL be Spanish.

#### Scenario: Cancel active cash hides artist
- **WHEN** an operator clicks "Cancelar efectivo" for a cash-`active` artist
- **THEN** `status` SHALL become `"canceled"`, `Artist.is_active` SHALL become `False`, the artist SHALL disappear from the public API, the message SHALL be "Suscripción en efectivo cancelada. El artista ya no es visible.", and the canceled emails SHALL be sent.

#### Scenario: Cash actions hidden for online rows
- **WHEN** an administrator opens an Artist change form whose subscription is `payment_method="online"` with any link or Stripe identifiers
- **THEN** none of "Marcar como efectivo", "Confirmar pago", "Cancelar efectivo" SHALL be shown.

### Requirement: Cash rows carry no Stripe identifiers
Cash rows SHALL NOT require or populate `stripe_customer_id` / `stripe_subscription_id` (both stay empty); `signup_url` stays empty so the "Copiar link" button never renders for cash. `raw_state` on cash transitions SHALL store a small audit dict (`{"cash": true, ...}`) instead of a Stripe object.

#### Scenario: Cash row has no Stripe linkage
- **WHEN** any cash transition completes
- **THEN** `stripe_customer_id` and `stripe_subscription_id` SHALL remain empty and `signup_url` SHALL remain empty.
