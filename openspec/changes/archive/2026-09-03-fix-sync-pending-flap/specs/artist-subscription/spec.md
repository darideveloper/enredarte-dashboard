## MODIFIED Requirements

### Requirement: Operator-controlled sync from Stripe
The system SHALL expose a per-subscription path that re-fetches Stripe state (Customer, Subscription, latest invoices) and updates the local `ArtistSubscription` row + `Artist.is_active` via `compute_is_active`, used as a manual salvavidas when a webhook is missed. The implementation MUST correctly handle the Stripe SDK `ListObject` return type from `Subscription.list` (accessing the subscriptions via `.data`, not via integer index on the ListObject itself) for both empty and non-empty results, MUST handle Stripe v15 `StripeObject` where `dict.get` is blocked (use `sget`/`to_plain_dict` via `obj[key]`/`getattr`, not `.get`), and MUST handle `Decimal` fields (`unit_amount_decimal` etc.) via `to_dict(for_json=True)` + `Decimal→str` so `JSONField` storage never raises `TypeError: Object of type Decimal is not JSON serializable`. When the customer holds zero subscriptions, the system SHALL NOT unconditionally mark a `PENDING` subscription as `CANCELED`; the empty-list → `CANCELED` transition SHALL apply only when the local `status != PENDING` (YAGNI guard).

#### Scenario: Manual sync reconciles state
- **WHEN** an operator clicks "Sincronizar desde Stripe" on an artist with `stripe_customer_id` whose customer holds an active subscription (including a `StripeObject` whose `.get` is blocked and whose payload contains `Decimal`)
- **THEN** the system SHALL call the Stripe API for the customer and `Subscription.list(customer, limit=1)`, read the first subscription from the `ListObject`'s `data` array, replace matching fields on `ArtistSubscription` via `sget`/`to_plain_dict(for_json=True)` (`apply_stripe_payload`), run `compute_is_active`, persist the resulting boolean to `Artist.is_active`, and update `last_synced_at` and `raw_state` as JSON-serializable plain `dict`.

#### Scenario: Manual sync for a never-subscribed artist
- **WHEN** an operator clicks "Sincronizar desde Stripe" but the artist has no `stripe_customer_id`
- **THEN** the system SHALL show an admin warning ("Este artista aún no tiene suscripción en Stripe.") and SHALL NOT call the Stripe API.

#### Scenario: Manual sync with zero subscriptions keeps PENDING
- **WHEN** an operator clicks "Sincronizar desde Stripe" on an artist whose `ArtistSubscription.status == PENDING` and whose Stripe customer exists but holds no subscriptions (`ListObject` with `data == []` or plain `[]`)
- **THEN** the system SHALL NOT change `status` (it SHALL remain `PENDING`), SHALL update `customer_email` (from `sget(customer,"email")` if present) and `last_synced_at`, SHALL re-derive `Artist.is_active` via `compute_is_active` (which returns `False` for `PENDING`), and SHALL show the admin success message with the unchanged status (`Pendiente de pago → Pendiente de pago`).

#### Scenario: Manual sync with zero subscriptions flips non-PENDING to CANCELED
- **WHEN** an operator clicks "Sincronizar desde Stripe" on an artist whose `ArtistSubscription.status != PENDING` (e.g., `ACTIVE`, `PAST_DUE`, `CANCELING`) and whose Stripe customer holds no subscriptions (`ListObject` with `data == []`)
- **THEN** the system SHALL set local `status="canceled"`, persist `Artist.is_active=False` via `compute_is_active`, and update `last_synced_at` / `customer_email`.

#### Scenario: Manual sync handles ListObject correctly
- **WHEN** `Subscription.list` returns a `ListObject` (real SDK, `stripe/_list_object.py:99`) rather than a plain list
- **THEN** the system SHALL NOT raise `KeyError` on integer indexing and SHALL read the subscription from `ListObject.data[0]` (or its empty check via `not ListObject.data`), so operators never see the crash at `/admin/artworks/artist/<id>/sync-from-stripe/`.

#### Scenario: Manual sync handles StripeObject without dict.get
- **WHEN** `ListObject.data[0]` is a `StripeObject` (`stripe/_stripe_object.py:163` blocks `dict.get` in v15)
- **THEN** the system SHALL NOT raise `AttributeError: 'get' is a dict method` and SHALL read fields via `sget` (`obj[key]` then `getattr`) and store `raw_state` via `to_plain_dict`, so sync succeeds for both plain `dict` mocks and real `StripeObject`.

#### Scenario: Manual sync handles Decimal payloads
- **WHEN** the Stripe subscription/invoice payload contains `Decimal` (e.g., `unit_amount_decimal: Decimal("9.99")` in v15)
- **THEN** the system SHALL NOT raise `TypeError: Object of type Decimal is not JSON serializable` at `json/encoder.py:180` and SHALL persist `raw_state` as JSON-serializable plain `dict` via `to_plain_dict(for_json=True)` / `_convert_decimals` (`Decimal→str`).
