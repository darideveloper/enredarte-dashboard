# artist-payment-method-filter

## Purpose
Defines how operators filter artists by subscription payment method (`online`/`cash`/`none`) and identify the method at a glance via the enriched `Suscripción` badge on the Artist changelist, plus a payment-method filter on the subscription changelist.

## Requirements

### Requirement: Artist payment-method filter at top of changelist
The system SHALL provide `ArtistPaymentMethodFilter` on `ArtistAdmin` as the **first** entry of `list_filter`, with title `Método de pago`, parameter `payment_method`, and lookups `online→En línea`, `cash→Efectivo`, `none→Sin suscripción`, implemented with `Exists`/`OuterRef` subqueries (no joins, no `distinct()`).

#### Scenario: Filter placed top
- **WHEN** an administrator opens the Artist changelist
- **THEN** `Método de pago` SHALL be the first filter in the sidebar, before `is_active`/`created_at`/location/artworks filters.

#### Scenario: Filtering online artists
- **WHEN** an administrator selects `En línea`
- **THEN** only artists having an `ArtistSubscription` with `payment_method="online"` SHALL be shown (artists with no subscription SHALL be excluded).

#### Scenario: Filtering cash artists
- **WHEN** an administrator selects `Efectivo`
- **THEN** only artists having an `ArtistSubscription` with `payment_method="cash"` SHALL be shown (including cash-`canceled` rows; method and status are independent).

#### Scenario: Filtering artists without subscription
- **WHEN** an administrator selects `Sin suscripción`
- **THEN** only artists having no `ArtistSubscription` row SHALL be shown.

#### Scenario: No filter selected shows all
- **WHEN** no `payment_method` lookup is selected
- **THEN** the changelist SHALL be unfiltered by payment method.

### Requirement: Payment method visible in Suscripción badge
The system SHALL prefix the `ArtistAdmin` `Suscripción` badge with the payment method (`Efectivo · {status}` / `En línea · {status}`), keeping the existing per-status colors; artists without a subscription SHALL still render muted `Sin suscripción`. The badge SHALL render from the `_payment_method` annotation (no per-row query) and SHALL fall back to the status-only label when the annotation is absent.

#### Scenario: Cash artist badge
- **WHEN** an administrator views an artist with cash-`active` subscription
- **THEN** the badge SHALL read `Efectivo · Activa` with the active (green) style.

#### Scenario: Online artist badge
- **WHEN** an administrator views an artist with online-`pending` subscription
- **THEN** the badge SHALL read `En línea · Pendiente de pago` with the pending style.

#### Scenario: Artist without subscription
- **WHEN** an administrator views an artist with no subscription row
- **THEN** the badge SHALL render muted `Sin suscripción` (no prefix).

### Requirement: Subscription changelist exposes payment-method filter
The system SHALL add `payment_method` to `ArtistSubscriptionAdmin.list_filter` (direct field filter) so operators can isolate `En línea` / `Efectivo` rows there too.

#### Scenario: Filtering subscriptions by method
- **WHEN** an administrator selects `Efectivo` in the subscription changelist
- **THEN** only `ArtistSubscription` rows with `payment_method="cash"` SHALL be shown.
