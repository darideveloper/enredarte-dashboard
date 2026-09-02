## MODIFIED Requirements

### Requirement: Sync from Stripe endpoint
The system SHALL expose `POST /subscriptions/admin/artists/<artist_id>/sync-from-stripe/` (implemented as `ArtistAdmin.sync_from_stripe` at `artworks/admin.py:490`) which fetches the latest customer and subscription state from the Stripe API and updates the local `ArtistSubscription` row + `Artist.is_active` via `compute_is_active`. The endpoint MUST correctly handle the `ListObject` return type from `stripe.Subscription.list` (use `.data` for emptiness and for the first element), MUST handle `StripeObject` without `dict.get` via `sget`/`to_plain_dict`, and MUST handle `Decimal` payloads via `to_dict(for_json=True)` + `_convert_decimals`.

#### Scenario: Sync corrects a missed webhook
- **WHEN** a staff member clicks "Sincronizar desde Stripe" for an artist whose local state is older than what Stripe reports and `Subscription.list` returns `ListObject(data=[active_sub])` (including `StripeObject` with blocked `.get` and `Decimal`)
- **THEN** the system SHALL update `status`, `current_period_end`, `cancel_at_period_end` to match `ListObject.data[0]` via `sget`/`to_plain_dict`, persist the resulting `Artist.is_active`, update `last_synced_at`, and show a success message including the previous vs new `status` (no `KeyError`, no `AttributeError: 'get' is a dict method`, no `TypeError: Decimal...`).

#### Scenario: Sync warns for never-subscribed artist
- **WHEN** a staff member clicks "Sincronizar desde Stripe" for an artist with no `stripe_customer_id`
- **THEN** the system SHALL show the admin warning ("Este artista aún no tiene un customer en Stripe.") and SHALL NOT call the Stripe API.

#### Scenario: Sync after Stripe migration reads ListObject correctly
- **WHEN** the live webhook was migrated to `https://dashboard.enredarte.mx/webhooks/stripe/` and a subsequent `sync-from-stripe` call hits the same customer with `stripe>=15.5.1` (`StripeObject` + `Decimal`)
- **THEN** the endpoint SHALL still read `Subscription.list` as `ListObject` and return `302` (not `KeyError` at `stripe/_list_object.py:103`, not `AttributeError` at `stripe/_stripe_object.py:163` via `sget`, not `TypeError` at `json/encoder.py:180` via `to_plain_dict(for_json=True)` + `Decimal→str`), regardless of whether the customer has 0 or 1 subscription.

#### Scenario: Sync persists JSON-serializable raw_state
- **WHEN** `apply_stripe_payload` or webhook `invoice.payment_succeeded/failed` stores `raw_state`/`payload` containing `Decimal` or `StripeObject`
- **THEN** the system SHALL store `JSONField` via `to_plain_dict` (`for_json=True` + `_convert_decimals`) so `json.dumps` succeeds and the admin `raw_state` is inspectable.
