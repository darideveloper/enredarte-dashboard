## ADDED Requirements

### Requirement: Payment-method filtering and badge stay query-safe
The system SHALL implement `ArtistPaymentMethodFilter` with `Exists`/`OuterRef` subqueries (no joins, no `distinct()`, ordering/pagination preserved) and SHALL render the payment-method badge prefix from the `_payment_method` `Subquery` annotation in `ArtistAdmin.get_queryset()`, so the Artist changelist issues no per-row subscription query.

#### Scenario: Payment-method filter uses EXISTS
- **WHEN** an administrator selects any `Método de pago` lookup
- **THEN** the changelist SHALL include only matching artists, without duplicates and with default ordering/pagination preserved.

#### Scenario: Badge renders without per-row queries
- **WHEN** an administrator opens the Artist changelist with 50 rows per page
- **THEN** every `Suscripción` badge (including the payment-method prefix) SHALL be populated from annotations attached to the main query, and no additional subscription query SHALL be executed per displayed artist.
