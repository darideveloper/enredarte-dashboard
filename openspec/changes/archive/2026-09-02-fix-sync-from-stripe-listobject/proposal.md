## Why

The admin action `Sincronizar desde Stripe` (`GET /admin/artworks/artist/<id>/sync-from-stripe/`, `artworks/admin.py:490`) crashed in production in three sequential stages after the Stripe SDK upgrade to `stripe>=15.5.1` (`requirements.txt:29`, `stripe/_stripe_object.py:163`, `stripe/_list_object.py:99`):

1. `KeyError: "You tried to access the 0 index, but ListObject types only support string keys. (HINT: You likely want to call .data[0])"` — `artworks/admin.py:504` did `subs[0]` on `stripe_client.list_subscriptions` (`subscriptions/services/stripe_client.py:79`) which returns `ListObject` with `.data`, not a plain `list`.
2. `AttributeError: 'get' is a dict method, but a Subscription is not a dict. Use .to_dict()` — `subscriptions/models.py:271` `apply_stripe_payload` used `stripe_sub.get(...)` on a real `StripeObject` (`Subscription` from `ListObject.data[0]`). Works for plain `dict` mocks (`subscriptions/tests.py:524,547`) but blocked in `stripe>=15` (`_stripe_object.py:163`).
3. `TypeError: Object of type Decimal is not JSON serializable` — `stripe>=15` returns `Decimal` for `unit_amount_decimal`/`fx_rate` (`_stripe_object.py` + `json/encoder.py:180`); `subscriptions/models.py:279` `raw_state` and `subscriptions/webhooks.py:186` `payload` were plain `dict(self)` / `event.to_dict()` without `for_json=True` → `JSONField` failed.

Existing tests masked all three: they mock `list_subscriptions` with plain `list` and `apply_stripe_payload` with plain `dict`, so green locally (`stripe==11.1.0` allows `.get`) but `500` in prod. The webhook-driven happy path works, but the manual salvavidas is broken — exactly when the operator needs it (missed webhook, stale state). Fix now before operators lose trust.

## What Changes

- **BREAKING: none** — pure bugfix, no API or schema change.
- Fix `ArtistAdmin.sync_from_stripe` (`artworks/admin.py:504-513`) to handle the real `ListObject`: `subs_data = subs.data if hasattr(subs,"data") else subs; if not subs_data: CANCELED else: apply_stripe_payload(subs_data[0])` so `ListObject` (real SDK) and plain-list mocks both work.
- Introduce DRY compat layer `subscriptions/services/stripe_compat.py:10` `sget` (version-agnostic `get` via `obj[key]` → `getattr`) and `to_plain_dict` (`to_dict(for_json=True)` fallback + `_convert_decimals` `Decimal→str` recursion) for `stripe>=11` and `>=15`.
- Use `sget`/`to_plain_dict` in `subscriptions/models.py:273` `apply_stripe_payload`/`upsert_from_stripe:301`, `subscriptions/admin.py:113` BillingPlan live preview, `subscriptions/services/plan_sync.py:43,52` product/price id, and `subscriptions/webhooks.py:167,111,131` `event.to_dict(for_json=True)` + `to_plain_dict` for `invoice`/`payload` `JSONField` so `Decimal` never hits `json.dumps`.
- Normalize `subscriptions/services/stripe_client.py:list_subscriptions` docstring to make the contract explicit (returns Stripe `ListObject`; caller must use `.data`). Wrapper keeps returning `ListObject` — admin unwraps (design D1).
- Add regression tests: `ListObject`-shaped mock with string-only `__getitem__` guard (`subscriptions/tests.py:69` `_make_list_object`) for empty and single-active, `_make_get_blocked_subscription` (`subscriptions/tests.py:95` whose `.get` raises like `stripe>=15`), real `stripe.Subscription.construct_from` paths, and `Decimal` `json.dumps` round-trip (`test_to_plain_dict_handles_decimal`, `test_apply_payload_with_decimal_is_json_serializable`), plus `ListObject+blocked` (`test_sync_from_stripe_with_listobject_and_get_blocked_reconciles`).
- No env, routing, or webhook URL changes. Webhook endpoint `https://dashboard.enredarte.mx/webhooks/stripe/` (`we_1U9tgOPSaJ0P1XliaMMZOAJD`) unrelated.

## Capabilities

### New Capabilities
- _none_ — this is a correctness fix, not a new feature (DRY `stripe_compat` is internal helper, not a capability).

### Modified Capabilities
- `artist-subscription`: The "Operator-controlled sync from Stripe" requirement already promises the salvavidas works. The fix restores behavior for customers with subscriptions and ensures `StripeObject` without `dict.get` and `Decimal` payloads are handled (previously crashed on `subs[0]` then `stripe_sub.get` then `Decimal`).
- `artist-subscription-actions`: The "Sync from Stripe action" scenarios (sync updates state / sync without customer shows warning) must pass against the real `ListObject` shape, against a `StripeObject` with blocked `.get`, and against `Decimal` payloads — not only plain `list`/`dict` mocks.
- `subscription-admin-controls`: The `POST /subscriptions/admin/artists/<artist_id>/sync-from-stripe/` (implemented as `ArtistAdmin.sync_from_stripe`) contract — fetch customer + list subscriptions + update local row via `compute_is_active` — must handle `ListObject.data` and v15 `StripeObject.get`/`Decimal` correctly.

## Impact

- **Affected code:** `artworks/admin.py` (one action, 3 lines + `sget` customer email), `subscriptions/services/stripe_compat.py` (new file: `sget`, `to_plain_dict`, `_convert_decimals`), `subscriptions/models.py` (`apply_stripe_payload`/`upsert_from_stripe` via `sget`/`to_plain_dict`), `subscriptions/services/stripe_client.py` (docstring only), `subscriptions/admin.py` (`BillingPlanAdmin.change_view` via `sget`), `subscriptions/services/plan_sync.py` (`sget` product/price id), `subscriptions/webhooks.py` (`to_plain_dict(for_json=True)` for event/invoice `payload`/`raw_state`), `subscriptions/tests.py` (adds ListObject, blocked-`get`, StripeObject, and Decimal mock cases). No migrations, no settings, no Stripe Dashboard changes.
- **Systems:** Django admin (`/admin/artworks/artist/*/change/sync-from-stripe/`, `/admin/subscriptions/billingplan/*/change/` live preview) and webhook `POST /webhooks/stripe/` (`raw_state`/`payload` `JSONField`); public API and webhook URL untouched.
- **Risks:** Minimal — DRY `hasattr(subs,"data")` guard backward-compatible with plain-list mocks; `sget` via `obj[key]`→`getattr` handles both `dict` and `StripeObject` (`11.x` and `15.x`); `to_plain_dict(for_json=True)`+`Decimal→str` handles `11.x` no-Decimal and `15.x` `Decimal`; verified against `stripe==11.1.0` locally and `stripe>=15.5.1` docs (`/stripe/stripe-python` v15: `StripeObject` no longer `dict`, `Decimal` via `for_json`). `73/73` `subscriptions` tests green (was `65`).
