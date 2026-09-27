## ADDED Requirements

### Requirement: StripeEvent owned by core with preserved history

The system SHALL provide `core.models.StripeEvent` with fields identical to the current `subscriptions.models.StripeEvent` (`event_id` unique, `event_type`, `received_at`, `processed_at`, `payload`, `error`, ordering by `-received_at`, content-based `__str__`). A data migration SHALL copy every row from `subscriptions_stripeevent` to the new table (plain `bulk_create` preserving `event_id`/`event_type`/`received_at`/`processed_at`/`payload`/`error`, in a `subscriptions` migration depending on `core.0001_initial`) and assert row-count equality, then remove the old model. `subscriptions.models.StripeEvent` SHALL NOT exist after the change. The Django admin registration (`StripeEventAdmin`, read-only audit) SHALL move to `core/admin.py` with identical list display, filters, and permissions.

#### Scenario: History survives the move

- **WHEN** the migration runs on a database containing N `subscriptions_stripeevent` rows
- **THEN** `core_stripeevent` SHALL contain the same N rows with identical `event_id`, `event_type`, `payload`, and timestamps.

#### Scenario: Reverse migration is safe before new events

- **WHEN** the migration is reversed before any new event was appended after the move
- **THEN** the rows SHALL return to `subscriptions_stripeevent` with no data loss; if new events exist, the reverse SHALL refuse rather than silently drop them.

#### Scenario: Idempotency lock preserved

- **WHEN** two identical webhook deliveries arrive concurrently after the move
- **THEN** the second INSERT SHALL raise `IntegrityError` on the `core_stripeevent` unique index and the endpoint SHALL return 200 without running the handler.

### Requirement: Shared Stripe helpers owned by core

The system SHALL provide `epoch_to_datetime` from `core.stripe_utils` and `sget` / `to_plain_dict` from `core.stripe_compat`, with behavior identical to today. `subscriptions/services/stripe_compat.py` SHALL NOT exist after the change. All import sites in `subscriptions/` (`models`, `webhooks`, `plan_sync`, `admin`) and `artworks/` sale modules (`stripe_orders`, `sale_notifications`, `order_webhooks`, `views` sale paths, `services`, commands) SHALL import from `core`.

#### Scenario: Shared helpers resolve from core

- **WHEN** any subscription or artwork module calls `sget`, `to_plain_dict`, or `epoch_to_datetime`
- **THEN** the symbol SHALL be imported from `core.stripe_compat` / `core.stripe_utils`, and no copy SHALL remain under `subscriptions/`.

### Requirement: Single Stripe SDK initialization owned by core

The system SHALL provide `core/stripe.py` that, on import, sets `stripe.api_key = settings.STRIPE_SECRET_KEY` and `stripe.api_version = settings.STRIPE_API_VERSION` when configured, and performs the `STRIPE_*` presence check. Both `artworks/stripe_orders.py` and `subscriptions/services/stripe_client.py` SHALL import it before any Stripe SDK call, so an artwork-only path (management commands, `buy`) can never issue an unauthenticated request.

#### Scenario: Artwork-only command authenticates Stripe

- **WHEN** `manage.py sync_orders_from_stripe` runs in an environment with `STRIPE_SECRET_KEY` set, without importing any subscription module
- **THEN** `stripe.api_key` SHALL be set from `core.stripe` and the saved-checkout retrieval SHALL be authenticated.

#### Scenario: Missing key refuses to call Stripe

- **WHEN** a Stripe call path runs with `STRIPE_SECRET_KEY` empty outside dev
- **THEN** the shared presence check SHALL raise a configuration error rather than issuing an unauthenticated Stripe request.

### Requirement: No module-level import cycle between domains

The system SHALL NOT introduce a module-level import cycle: `artworks` sale modules SHALL import zero from `subscriptions`, and `subscriptions/webhooks.py` SHALL reference artwork handlers only at dispatch time (inside the handler call), never as a required top-level construct that would force `artworks` to import `subscriptions`. Legitimate artist-membership admin usage in `artworks/admin.py` importing subscription-domain services is explicitly out of scope for this rule.

#### Scenario: Sale modules stay subscription-free

- **WHEN** grepping `artworks/stripe_orders.py`, `artworks/sale_notifications.py`, `artworks/order_webhooks.py`, and the sale code paths of `artworks/views.py` / `artworks/services.py` / sale management commands
- **THEN** zero `from subscriptions` / `import subscriptions` matches SHALL remain.

#### Scenario: Website boots without circular import

- **WHEN** Django loads URLConf (`subscriptions/webhooks.py`) and admin autodiscovery (`artworks/admin.py`, `core/admin.py`)
- **THEN** startup SHALL complete without `ImproperlyConfigured` or circular-import errors.
