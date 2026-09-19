## MODIFIED Requirements

### Requirement: Confirm cash payment (active, indefinite)
The system SHALL provide a "Confirmar pago" changeform action, visible for cash rows with `status="pending"`, `"active"`, or `"past_due"`. On execution it SHALL set `status="active"`, stamp `cash_last_paid_at = today`, set `current_period_end = max(today, current renew) + 1 calendar month` (initializing both dates when renew is null), persist `is_active=True` via `compute_is_active`, stamp `last_synced_at`, record `{"cash": true, "confirmed_by": <username>}` provenance in `raw_state`, fire the active cash emails, and show `messages.success("Pago en efectivo confirmado. El artista ya es visible.")`. Each execution counts as one monthly payment: re-confirming an `active` row extends the renew date and re-sends the receipt (no duplicate suppression). Direct URL execution for non-eligible rows is refused at the permission boundary (403). All operator-visible messages SHALL be Spanish.

#### Scenario: Confirm cash payment makes artist visible indefinitely
- **WHEN** an operator clicks "Confirmar pago" for a cash-`pending` artist
- **THEN** `status` SHALL become `"active"`, `Artist.is_active` SHALL become `True`, the artist SHALL appear in `GET /api/artworks/artists/`, `cash_last_paid_at` SHALL be today, `current_period_end` SHALL be today + 1 calendar month, the message SHALL be "Pago en efectivo confirmado. El artista ya es visible.", and the active emails SHALL be sent.

#### Scenario: Re-confirm during grace recovers to active
- **WHEN** an operator clicks "Confirmar pago" for a cash-`past_due` artist inside the grace window
- **THEN** `status` SHALL return to `"active"`, the renew date SHALL extend one month, and the receipt SHALL be sent again.

#### Scenario: Double confirm extends instead of no-op
- **WHEN** an operator clicks "Confirmar pago" for an already cash-`active` artist
- **THEN** the renew date SHALL extend one further month and the receipt SHALL be sent (each click = one payment). The old no-op behavior is removed.

### Requirement: Cancel cash subscription
The system SHALL provide a "Cancelar efectivo" changeform action, visible for cash rows with `status="pending"`, `"active"`, or `"past_due"`. On execution it SHALL set `status="canceled"`, persist `is_active=False` via `compute_is_active`, stamp `last_synced_at`, fire the canceled cash emails, and show `messages.success("Suscripción en efectivo cancelada. El artista ya no es visible.")`. All operator-visible messages SHALL be Spanish.

#### Scenario: Cancel active cash hides artist
- **WHEN** an operator clicks "Cancelar efectivo" for a cash-`active` artist
- **THEN** `status` SHALL become `"canceled"`, `Artist.is_active` SHALL become `False`, the artist SHALL disappear from the public API, the message SHALL be "Suscripción en efectivo cancelada. El artista ya no es visible.", and the canceled emails SHALL be sent.

#### Scenario: Cancel during grace hides immediately
- **WHEN** an operator clicks "Cancelar efectivo" for a cash-`past_due` artist
- **THEN** `status` SHALL become `"canceled"` at once (no waiting for grace end) with the same message and emails.
