## 1. Fix sync-from-stripe ListObject handling

- [x] 1.1 Edit `artworks/admin.py:490-524` `ArtistAdmin.sync_from_stripe`: replace `subs = stripe_client.list_subscriptions(...); if not subs: / else: subs[0]` with `subs_data = subs.data if hasattr(subs,"data") else subs; if not subs_data: ... else: sub.apply_stripe_payload(subs_data[0])` so `ListObject` (real SDK) and plain-list mocks both work; verify `stripe/_list_object.py:99` guard no longer hit.
- [x] 1.2 Clarify `subscriptions/services/stripe_client.py:79-85` `list_subscriptions` docstring to state it returns a Stripe `ListObject` (caller must use `.data`); wrapper keeps returning `ListObject` — no behavior change, docs only.
- [x] 1.3 Fix `subscriptions/services/stripe_compat.py` DRY compat helper: add `sget(obj,key,default)` (`obj[key]`→`KeyError→default`, `TypeError/AttributeError→getattr`) and `to_plain_dict` (`to_dict(for_json=True)` fallback + `_convert_decimals` `Decimal→str` recursion) for `stripe>=11` and `>=15`.
- [x] 1.4 Edit `subscriptions/models.py:273` `apply_stripe_payload` + `293` `upsert_from_stripe` to use `sget` for `id`/`customer`/`customer_email`/`current_period_end`/`cancel_at_period_end`/`status` and `to_plain_dict` for `raw_state` (not `stripe_sub.get` / `dict(self)`); ensures `StripeObject` without `get` + `Decimal` never `500`/`TypeError`.
- [x] 1.5 Edit `subscriptions/admin.py:113` `BillingPlanAdmin.change_view` + `subscriptions/services/plan_sync.py:43,52` to use `sget` for `price`/`product` fields; edit `subscriptions/webhooks.py:167,111,131,186` to use `event.to_dict(for_json=True)`→`to_plain_dict` and `to_plain_dict(invoice)` for `payload`/`raw_state` `JSONField`.

## 2. Tests — reproduce the real SDK shape

- [x] 2.1 Add a `ListObject`-shaped mock test for `sync_from_stripe` with one active sub: `type("LO", (), {"data":[make_subscription(status="active", period_end=future_epoch())]})` plus string-only `__getitem__` to reproduce `stripe/_list_object.py:99`, assert `302` and `ACTIVE` / `is_active=True`.
- [x] 2.2 Add a `ListObject` empty mock test: `type("LO", (), {"data":[]})` assert `302` and `CANCELED` / `is_active=False`.
- [x] 2.3 Add `get`-blocked and `StripeObject` mock tests: `_make_get_blocked_subscription` (`_Blocked(dict)` whose `.get` raises `AttributeError: 'get' is a dict method`) + `stripe.Subscription.construct_from` paths: `test_sget_get_blocked`, `test_sget_stripe_object`, `test_apply_payload_with_get_blocked`, `test_apply_payload_with_stripe_object`, `test_sync_from_stripe_with_listobject_and_get_blocked_reconciles`; document why plain `list`/`dict` mocks stay backward-compatible via `hasattr`+`sget`.
- [x] 2.4 Add `Decimal` JSON tests: `_convert_decimals`/`to_plain_dict` with nested `Decimal("9.99")`/`Decimal("1.234")` assert `json.dumps` succeeds and `Decimal→str`; `test_apply_payload_with_decimal_is_json_serializable`.
- [x] 2.5 Keep existing plain-list/dict mocks green (`subscriptions/tests.py:510-554`); the dual-shape `hasattr`+`sget` guards must pass both — document in `_make_list_object`/`stripe_compat` docstring why mocks stay plain-list backward-compatible.

## 3. Verification

- [x] 3.1 Run `python manage.py test subscriptions.tests.AdminEndpointTest.test_sync_from_stripe_* subscriptions.tests.StripeCompatTest -v 2` — plain-list, ListObject, blocked-`get`, StripeObject, Decimal JSON all green.
- [x] 3.2 Run full `python manage.py test subscriptions -v 2` — `73/73` (was `65`, +8: 5 `StripeCompatTest` + 1 `ListObject+blocked` + 2 `Decimal`) with no webhook/regression, no `KeyError`/`AttributeError`/`TypeError: Decimal...`.
- [x] 3.3 Manual prod check after deploy: `GET /admin/artworks/artist/5/sync-from-stripe/` → expect `302` with `Suscripción sincronizada: ... → ...` (previously `KeyError` at `_list_object.py:103`, then `AttributeError` at `_stripe_object.py:163`, then `TypeError` at `json/encoder.py:180`); confirm for both a customer with 0 subs and with 1 active sub including `Decimal` payload.
