## MODIFIED Requirements

### Requirement: Subscription status badge on Artist changelist
The system SHALL add a read-only "Suscripción" badge to the `ArtistAdmin` changelist showing the `ArtistSubscription` payment method plus `status` display label in Spanish — `Efectivo · {status}` for cash rows, `En línea · {status}` for online rows — plus a colored register-style badge variant per state (`pending`, `active`, `past_due`, `canceling`, `canceled`), and the literal "Sin suscripción" when the artist has no subscription row.

#### Scenario: Display without subscription
- **WHEN** an administrator opens the Artist changelist for an artist without an `ArtistSubscription`
- **THEN** the "Suscripción" column SHALL render "Sin suscripción" in muted text.

#### Scenario: Display with active subscription
- **WHEN** an administrator opens the Artist changelist for an artist with `ArtistSubscription.status="active"`
- **THEN** the "Suscripción" column SHALL render a green badge reading "Activa" prefixed by the payment method ("Efectivo · Activa" or "En línea · Activa").

#### Scenario: Display during friendly cancellation
- **WHEN** an administrator opens the Artist changelist for an artist with `ArtistSubscription.status="canceling"`
- **THEN** the "Suscripción" column SHALL render an amber badge reading "Cancelada, vigente hasta fin de período" prefixed by the payment method.

#### Scenario: Display after lapse
- **WHEN** an administrator opens the Artist changelist for an artist with `ArtistSubscription.status="canceled"` or past-grace `past_due`
- **THEN** the "Suscripción" column SHALL render a red badge reading accordingly, prefixed by the payment method.

## ADDED Requirements

### Requirement: Payment-method filter first on Artist changelist
The system SHALL render `ArtistPaymentMethodFilter` (`Método de pago`: `En línea` / `Efectivo` / `Sin suscripción`) as the first entry of `ArtistAdmin.list_filter`, before all existing filters.

#### Scenario: Filter order
- **WHEN** an administrator opens the Artist changelist
- **THEN** the first filter in the sidebar SHALL be `Método de pago`.
