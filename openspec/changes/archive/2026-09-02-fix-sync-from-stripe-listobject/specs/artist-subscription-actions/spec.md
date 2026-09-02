## MODIFIED Requirements

### Requirement: Sync from Stripe action
The system SHALL provide a "Sincronizar desde Stripe" changeform action on the Artist admin change page that re-fetches the customer and subscription state from the Stripe API and updates the local `ArtistSubscription` and `Artist.is_active` accordingly. The action SHALL always be visible. The implementation MUST handle the Stripe SDK `ListObject` shape (`Subscription.list` returns `ListObject` with `.data`, not a plain `list`) so the action succeeds for both customers with and without subscriptions, MUST handle Stripe v15 `StripeObject` without `dict.get` via `sget`/`to_plain_dict`, and MUST handle `Decimal` payloads via `to_dict(for_json=True)`.

#### Scenario: Sync updates subscription state
- **WHEN** an administrator clicks "Sincronizar desde Stripe" for an artist with a `stripe_customer_id` whose `Subscription.list` returns a `ListObject` with one active subscription (including a `StripeObject` with blocked `.get` and `Decimal`)
- **THEN** the system SHALL fetch the customer and `ListObject`, extract the subscription from `ListObject.data[0]` via `sget`/`to_plain_dict`, update the local `ArtistSubscription` fields via `apply_stripe_payload` (using `sget` and `to_plain_dict(for_json=True)`), recompute `Artist.is_active` via `compute_is_active`, and redirect with a success message showing the status change (no `KeyError` at `stripe/_list_object.py:99`, no `AttributeError` at `_stripe_object.py:163`, no `TypeError: Decimal...`).

#### Scenario: Sync without customer shows warning
- **WHEN** an administrator clicks "Sincronizar desde Stripe" for an artist without a `stripe_customer_id`
- **THEN** the system SHALL display a warning message and redirect back to the change form without calling the Stripe API.

#### Scenario: Sync does not crash on ListObject indexing
- **WHEN** `Subscription.list` returns a `ListObject` (real SDK) for a customer with subscriptions
- **THEN** the action SHALL NOT attempt `ListObject[0]` (which raises `KeyError` at `stripe/_list_object.py:99`) and SHALL use `ListObject.data[0]` (via `subs.data if hasattr(subs,"data") else subs`) so the request returns `302` instead of `500`.

#### Scenario: Sync handles empty ListObject without crash
- **WHEN** `Subscription.list` returns a `ListObject` with `data == []` (customer exists, no subscriptions)
- **THEN** the system SHALL treat it as empty (check `not ListObject.data` / `not subs_data`) and set local `status="canceled"` without raising.

#### Scenario: Sync does not crash on StripeObject.get
- **WHEN** `ListObject.data[0]` is a `StripeObject` with blocked `dict.get` (`stripe>=15`, `stripe/_stripe_object.py:163`)
- **THEN** the action SHALL NOT call `stripe_sub.get(...)` and SHALL use `sget` (`obj[key]` then `getattr`) / `to_plain_dict`, so the request returns `302` (tested with `_make_get_blocked_subscription` and `stripe.Subscription.construct_from`).

#### Scenario: Sync handles Decimal in Stripe payload
- **WHEN** the returned subscription contains `Decimal` fields (`unit_amount_decimal`, `fx_rate`, etc.)
- **THEN** the action SHALL persist `raw_state` as `to_plain_dict(for_json=True)` with `Decimal→str` conversion, so `JSONField` save does not raise `TypeError: Object of type Decimal is not JSON serializable` at `json/encoder.py:180`.

