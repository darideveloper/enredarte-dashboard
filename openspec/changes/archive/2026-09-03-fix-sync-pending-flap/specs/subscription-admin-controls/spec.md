## MODIFIED Requirements

### Requirement: Sync from Stripe endpoint
The system SHALL expose `POST /subscriptions/admin/artists/<artist_id>/sync-from-stripe/` (implemented as `ArtistAdmin.sync_from_stripe` at `artworks/admin.py:490` via Unfold `actions_detail` `@action url_path="sync-from-stripe"` at `/admin/artworks/artist/<pk>/change/sync-from-stripe/`) which fetches the latest customer and subscription state from the Stripe API and updates the local `ArtistSubscription` row + `Artist.is_active` via `compute_is_active`. The endpoint MUST correctly handle the `ListObject` return type from `stripe.Subscription.list` (use `.data` for emptiness and for the first element) and MUST handle `StripeObject` without `dict.get` via `sget`/`to_plain_dict(for_json=True)` including `Decimal` fields. When the customer holds zero subscriptions, the endpoint SHALL apply the conditional rule: if local `status == PENDING` keep `PENDING` (still `is_active=False`); only if `status != PENDING` set `CANCELED` (true deletion). On `StripeError`, the endpoint SHALL log `warning`, show `messages.error("Stripe no respondió: …")`, and SHALL return `302` without `500` or partial DB mutation. The endpoint SHALL unwrap an expanded `customer` expanded object to `cus_xxx` and SHALL single-save (no double `save` at `artworks/admin.py:513-514`).

#### Scenario: Sync corrects a missed webhook
- **WHEN** a staff member clicks "Sincronizar desde Stripe" for an artist whose local state is older than what Stripe reports and `Subscription.list` returns `ListObject(data=[active_sub])` (including a `StripeObject` with blocked `.get` and `Decimal unit_amount_decimal`)
- **THEN** the system SHALL fetch `customer` via `sget(customer,"email")`, unwrap `ListObject.data[0]`, `apply_stripe_payload` via `sget`/`to_plain_dict`, persist `Artist.is_active`, update `last_synced_at`, and show success message `Suscripción sincronizada: {prev} → {new}` (no `KeyError` at `stripe/_list_object.py:99`, no `AttributeError` at `stripe/_stripe_object.py:163`, no `TypeError: Decimal is not JSON serializable`).

#### Scenario: Sync on PENDING with zero subscriptions keeps PENDING
- **WHEN** a staff member clicks "Sincronizar desde Stripe" for an artist whose `ArtistSubscription.status == PENDING` and whose Stripe customer holds no subscriptions (`ListObject` with `data == []` or plain `[]`)
- **THEN** the system SHALL NOT change `status` (remain `PENDING`), SHALL update `customer_email` and `last_synced_at`, SHALL re-derive `Artist.is_active=False` via `compute_is_active`, and SHALL show the success message with the unchanged display (`Pendiente de pago → Pendiente de pago`) instead of flapping to `Cancelada definitivamente`.

#### Scenario: Sync on non-PENDING with zero subscriptions flips to CANCELED
- **WHEN** a staff member clicks "Sincronizar desde Stripe" for an artist whose `ArtistSubscription.status != PENDING` (e.g., `ACTIVE`/`PAST_DUE`/`CANCELING`) and Stripe reports zero subscriptions
- **THEN** the system SHALL set `status="canceled"`, persist `Artist.is_active=False` via `compute_is_active`, and show `Suscripción sincronizada: {prev} → Cancelada definitivamente`.

#### Scenario: Sync warns for never-subscribed artist
- **WHEN** a staff member clicks "Sincronizar desde Stripe" for an artist with no `stripe_customer_id`
- **THEN** the system SHALL show the admin warning ("Este artista aún no tiene un customer en Stripe.") and SHALL NOT call the Stripe API.

#### Scenario: Sync remains resilient to Stripe failures
- **WHEN** `stripe.Customer.retrieve` or `stripe.Subscription.list` for the sync raises `stripe.error.StripeError` (deleted `cus_xxx`, network, auth, rate-limit, `Decimal` payload)
- **THEN** the system SHALL NOT return `500`; it SHALL `logger.warning` with `artist_id` and error, show `messages.error("Stripe no respondió: …")`, return `302` to the change form, and leave `ArtistSubscription`/`Artist.is_active`/`last_synced_at` unchanged.
