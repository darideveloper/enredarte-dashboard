## ADDED Requirements

### Requirement: Stripe observability via structured logging

The system SHALL provide structured logging for all Stripe money-path operations (webhook delivery, `ArtistAdmin` Stripe actions, `BillingPlan` price sync) via a `LOGGING` dict in `project/settings.py` (console handler, level `INFO` for `subscriptions`/`artworks` loggers, pass-through for optional `SENTRY_DSN`). Every Stripe API failure, webhook dispatch, and price-sync history creation SHALL be logged at appropriate level (`INFO` for success, `WARNING` for recoverable fallback, `EXCEPTION` for crash) so operators can trace money-path calls without inspecting Stripe Dashboard alone.

#### Scenario: Webhook handler logs dispatch and crash

- **WHEN** Stripe POSTs any event to `POST /webhooks/stripe/` and the handler succeeds
- **THEN** the system SHALL log at `INFO` the `event_id` and `event_type`, and the `StripeEvent` row SHALL be persisted with `processed_at=now()`.

- **WHEN** a handler raises an exception
- **THEN** the system SHALL log `logger.exception` with the `event_id`/`event_type` and SHALL return `500` (triggering Stripe retry). With the current single-transaction semantics, the `StripeEvent` row SHALL be rolled back (no `error` persisted) but the log line SHALL survive.

#### Scenario: Admin Stripe actions log failures

- **WHEN** any `ArtistAdmin` action (`generate_link`, `regenerate_link`, `open_portal`, `sync_from_stripe` at `artworks/admin.py:388,432,477,490`) catches `stripe.error.StripeError`
- **THEN** the system SHALL `logger.warning`/`exception` with `artist_id`, action name, and error message, and SHALL show `messages.error` with prefix `Stripe no respondió` while returning `302` to the change form (no `500`).

#### Scenario: BillingPlan preview and plan sync log

- **WHEN** `BillingPlanAdmin.change_view` (`subscriptions/admin.py:107`) fails to `retrieve_price` for the live preview
- **THEN** the system SHALL `logger.warning` with `stripe_price_id` and SHALL show `"(no se pudo confirmar)"` without raising.

- **WHEN** `plan_sync.ensure_stripe_price` archives the old price but Stripe fails after creating the new price
- **THEN** the system SHALL `logger.warning` with the orphan `new_price_id` and the `old_price_id` so the orphan is traceable, and SHALL propagate the `StripeError` so the DB stays unchanged (retry will create another price, documented).

#### Scenario: Stripe SDK version and webhook secret startup check

- **WHEN** the Django app starts with `ENV != "dev"` and `STRIPE_SECRET_KEY` is empty or `STRIPE_WEBHOOK_SECRET` does not start with `whsec_`
- **THEN** `subscriptions/apps.py:ready` SHALL raise `ImproperlyConfigured` (fails fast), preventing silent `400` on all webhooks (`stripe.Webhook.construct_event(..., "")`) and silent `stripe.api_key=None` drift.

#### Scenario: Stripe SDK version pin

- **WHEN** `requirements.txt` is installed
- **THEN** `stripe` SHALL be constrained to `>=15.5.1,<16` so a future `16.x` major (which may remove `stripe_id`/`to_dict_recursive` or change `StripeObject` again) requires explicit review, not silent auto-upgrade.
