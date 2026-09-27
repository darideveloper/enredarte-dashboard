## MODIFIED Requirements

### Requirement: StripeEvent admin registration
The system SHALL register `StripeEvent` (now `core.models.StripeEvent`) in the Django Unfold admin so an operator can browse the audit log: read-only list ordered by `received_at` desc, with a date filter and `event_type` filter, and a detail view showing the `payload` JSON. Registration SHALL live in `core/admin.py` after the model moves out of `subscriptions`; the admin's behavior, permissions, ordering, filters, and displayed columns SHALL be unchanged.

#### Scenario: Browsing recent webhook deliveries
- **WHEN** an administrator opens the "Eventos de Stripe" admin
- **THEN** rows MUST be ordered desc by `received_at`, MUST be read-only, and MUST show `event_type`, a short prefix of `event_id`, and `processed_at` (or `error` if any).

#### Scenario: Inspecting a failure
- **WHEN** an administrator opens a `StripeEvent` row whose `error` is non-empty
- **THEN** the change view SHALL show `error` and `payload` so the operator can diagnose the failure.

#### Scenario: Audit page survives the model move
- **WHEN** the app runs after `StripeEvent` moved to `core`
- **THEN** the "Eventos de Stripe" admin page SHALL still render with the same columns and filters, and existing rows SHALL remain visible.
