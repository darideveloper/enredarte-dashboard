## Context

`ArtistAdmin.sync_from_stripe` (`artworks/admin.py:490-524`) is the manual salvavidas for missed webhooks. It fetches the customer (`stripe_client.fetch_customer`) then `subs = stripe_client.list_subscriptions(customer_id, limit=1)` (`subscriptions/services/stripe_client.py:79-85` → `stripe.Subscription.list`) and branches on `if not subs: CANCELED else: apply_stripe_payload(subs[0])`. In production with `stripe>=15.5.1` (`requirements.txt:29`) three mismatches stack:

1. `Subscription.list` returns `ListObject` (`stripe/_list_object.py:29`): a `StripeObject(dict)` with `data: List[T]`, `has_more`, `url`, and `__getitem__` that rejects non-string keys (`:99-108` → `KeyError` with hint `You likely want to call .data[0]`). `ListObject.__len__` (`:118`) delegates to `len(data)`, so `bool(empty ListObject)==False` (empty works by accident) but `subs[0]` always crashes on non-empty — the reported `GET /admin/artworks/artist/5/sync-from-stripe/` error. `subscriptions/tests.py:510-554` mocks with plain `list` (`[make_subscription(...)]`, `[]`), so masked.
2. `subscriptions/models.py:271` `apply_stripe_payload` used `stripe_sub.get(...)` — works for plain `dict` mocks and `stripe==11.1.0` where `StripeObject` still allows `dict.get`, but `stripe>=15` blocks `dict` methods at `stripe/_stripe_object.py:163` → `AttributeError: 'get' is a dict method, but a Subscription is not a dict. Use .to_dict()`. `ListObject.data[0]` is a real `Subscription` `StripeObject`, so the second crash follows the first fix.
3. `stripe>=15` introduces `Decimal` for `unit_amount_decimal`/`fx_rate` (`_stripe_object.py` + migration guide `Decimal fields use Decimal instead of str` and `to_dict(for_json=True)`). `subscriptions/models.py:279` `raw_state = stripe_sub` (`dict(self)` path) and `subscriptions/webhooks.py:167` `event.to_dict()` without `for_json=True` leave `Decimal` in `JSONField` → `json/encoder.py:180` `TypeError: Object of type Decimal is not JSON serializable`.

Stakeholders: admin operators. Constraints: preserve empty→`CANCELED`/non-empty→`apply_stripe_payload` semantics, keep `StripeObject` compat for `stripe==11.1.0` and `>=15`, stay compatible with existing plain `list`/`dict` mocks, ensure `JSONField` `raw_state`/`payload` always JSON-serializable.

## Goals / Non-Goals

**Goals:**
- Make `sync_from_stripe` work against the real SDK `ListObject` for both 0 and 1 subscription, restoring `ArtistSubscription` + `Artist.is_active` via `compute_is_active`.
- Make `apply_stripe_payload`/`upsert_from_stripe` work for both plain `dict` mocks and real `StripeObject` without `dict.get` (via DRY `sget`), and make `raw_state`/`payload` `JSONField` safe for `Decimal` (via `to_plain_dict(for_json=True)` + `_convert_decimals`).
- Keep fix YAGNI/minimal (new `stripe_compat` helper + ~1-line call-site guards) and make each bug unmaskable in tests (ListObject guard, blocked-`get` mock, `Decimal` `json.dumps`).
- Preserve behavior for customers with 0 subs (`CANCELED`, `is_active=False`) and 1 active sub (`ACTIVE`, `is_active=True`, `last_synced_at` updated), and for pure `dict` mocks.

**Non-Goals:**
- Changing `BillingPlan` pricing, env vars, webhook routing, or public API.
- Adding pagination / `ListObject` auto-paging beyond `limit=1` (already correct).
- Refactoring other `stripe_client` methods or introducing `dj-stripe` or idempotency keys.
- Full logging/version-pin polish — deferred to `fix-stripe-prod-polish` (C1, W1, LOGGING, pin).

## Decisions

**D1 — Fix ListObject site: `artworks/admin.py:504-513` admin guard, not deep SDK rewrite.**
*Rationale:* Bug is at call-site. Smallest diff, lowest blast radius. Alternative `stripe_client.list_subscriptions` unwrapping to `list` (`.data`) would change the wrapper's contract and hide the real SDK type; we keep the wrapper returning `ListObject` (explicit contract) and let the caller unwrap.
*Alternatives:* (A) `return stripe.Subscription.list(...).data` in `stripe_client` — also fixes admin but silently changes API for future callers; (B) use `list(subs)[0]` via `ListObject.__iter__` (`:113`) — works but non-idiomatic vs SDK hint ` .data[0]`.

**D2 — Dual-shape handling `subs.data if hasattr(subs,"data") else subs`.**
*Rationale:* Tests currently return plain `list`; the fix must pass both real `ListObject` and those mocks without a flag-day test rewrite. `hasattr` is the stdlib one-liner (ponytail ladder).
*Alternative:* Force tests to return `ListObject.construct_from({"data": [...]})` only — cleaner but requires rewriting two test cases immediately; we keep backward compat and add one new `ListObject`-shaped case.

**D3 — Introduce DRY version-agnostic `sget`/`to_plain_dict` in `subscriptions/services/stripe_compat.py` and use in `apply_stripe_payload`/`upsert_from_stripe` (not keep `get` unchanged).**
*Rationale:* `stripe_sub.get(...)` works for `dict` and `11.x` `StripeObject` (dict subclass) but raises `AttributeError` in `15.x` (`_stripe_object.py:163`). Fixing per-file with `try: obj.get except AttributeError: obj[key]` violates DRY across `models.py`, `admin.py`, `plan_sync.py`. Single helper `sget` tries `obj[key]` (`__getitem__`, `_stripe_object.py:198`) then `KeyError→default`, `TypeError/AttributeError→getattr` fallback handles both plain `dict` and `StripeObject` (11 and 15). `upsert_from_stripe` also needs `sget` for `id`/`customer`.
*Alternative:* Keep `apply_stripe_payload` unchanged — rejected; repro with `ListObject.data[0]` as real `Subscription` proves crash; D3 corrects earlier assumption in v1 of this doc.

**D4 — Handle `Decimal` via `to_dict(for_json=True)` + recursive `Decimal→str`.**
*Rationale:* `stripe>=15` change `Decimal fields use Decimal instead of str` (`unit_amount_decimal`, `fx_rate`) + migration guide `to_dict(for_json=True) to handle Decimals` (`_stripe_object.py` `to_dict(recursive, for_json)`). `to_plain_dict` tries `obj.to_dict(for_json=True)` with `except TypeError: to_dict()` fallback for `11.x`, then `_convert_decimals` (`dict/list/tuple` recursion) → `str(Decimal)` ensures `JSONField` `raw_state` (`models.py:279`) and `StripeEvent.payload`/`invoice` `raw_state` (`webhooks.py:167,111,131`) never hit `TypeError` at `json/encoder.py:180`. `StripeObject is dict subclass` still true for `isinstance`, but `dict(obj)` is empty in 15.x, so `to_dict` is canonical.
*Alternative:* `json.dumps` with `default=str` — hides Decimal class but not DRY for `JSONField` storage; `to_plain_dict` centralizes.

**D5 — Test hardening: ListObject mock + blocked-`get` mock + Decimal `json.dumps`.**
*Rationale:* Existing plain `list`/`dict` mocks will continue to pass; new cases with `type("LO", (), {"data":[...]})` plus `__getitem__` guard reproduces `ListObject` crash, `type("Blocked", (dict,), {"get": raise AttributeError})` reproduces `StripeObject.get` blocked, and `Decimal("9.99")` nested in payload + `json.dumps(to_plain_dict(...))` reproduces `Decimal` JSON crash — without hitting live Stripe. Proves previous bugs would now fail.
*Alternative:* Only ListObject mock — insufficient; second and third crashes would re-mask.

## Risks / Trade-offs

- **Mock divergence → Mitigation:** Keep dual-shape `hasattr` guard, but new ListObject test fails fast if someone regresses to `subs[0]`; blocked-`get` test fails fast if someone reintroduces `.get`.
- **Relying on `__len__` for emptiness (`if not subs:`) is obscure:** Mitigated by switching to explicit `if not subs_data:` (checks `len(data)` clearly).
- **Future SDK major bump changes ListObject/StripeObject:** Mitigated by `hasattr` guard + `sget` (`obj[key]` then `getattr`) + `to_dict(for_json=True)` + docstring that caller must use `.data`/`sget`.
- **`Decimal` silently stringified (`"9.99"`) → Mitigation:** `to_plain_dict` doc notes wire format is `str(Decimal)`; `json/encoder.py` now succeeds, and downstream `map_stripe_status`/`compute_is_active` ignore Decimal fields.
- **Empty vs non-empty truthiness confusion:** Already mitigated — empty `ListObject` is falsy via `__len__`, but we no longer rely on it.

## Migration Plan

- No migrations. Deploy code, no Stripe Dashboard change. `requirements.txt` still `stripe>=15.5.1` (pin `<16` deferred to `fix-stripe-prod-polish`).
- Rollback: revert `artworks/admin.py:505` ListObject guard + `subscriptions/services/stripe_compat.py` + `subscriptions/models.py:273` `sget`/`to_plain_dict` + `subscriptions/webhooks.py:167` `for_json`; webhook endpoint (`we_1U9tg...`) unchanged.
- Verification: `python manage.py test subscriptions.tests.AdminEndpointTest.test_sync_from_stripe_* subscriptions.tests.StripeCompatTest -v 2` (plain-list, ListObject, blocked-`get`, StripeObject, Decimal JSON) + `python manage.py test subscriptions -v 2` (73/73, including `to_plain_dict` Decimal) + manual `GET /admin/artworks/artist/5/sync-from-stripe/` after deploy (expect `302` + `messages.success` + updated `last_synced_at`; no `KeyError` at `_list_object.py:99`, no `AttributeError` at `_stripe_object.py:163`, no `TypeError: Decimal...` at `json/encoder.py:180`).

## Open Questions

- None blocking. Optional follow-up (deferred to `fix-stripe-prod-polish`): `recurring.get` in `subscriptions/admin.py:116` still blocked via `isinstance` branch; `ArtistAdmin` 4 actions need `StripeError→messages.error+302`; add `LOGGING`, pin `<16`, startup check, small guards (invoice empty lines, expanded `customer`, `checkout.session.expired`).
