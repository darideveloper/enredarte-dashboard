## 1. Fix sync empty-list guard

- [x] 1.1 Edit `artworks/admin.py:531-540` `sync_from_stripe` empty branch: add `if sub.status != ArtistSubscription.Status.PENDING:` guard before setting `CANCELED`; else keep `PENDING` while still updating `customer_email` + `last_synced_at` and re-deriving `is_active` via `compute_is_active` (single `save(update_fields=[...])`, no double-save). Preserve `ListObject.data` vs plain list handling and `sget` for `customer.email`.
- [x] 1.2 Verify `artworks/admin.py` imports `ArtistSubscription` and `sget`/`compute_is_active` already in scope — no new imports needed.

## 2. Tests — correct bug codification

- [x] 2.1 Update `subscriptions/tests.py:665` `test_sync_from_stripe_no_subscriptions_sets_canceled` → assert `PENDING + []` stays `PENDING`, `customer_email` updated, `last_synced_at` set, `is_active == False` (via `compute_is_active`), success message shows `Pendiente de pago → Pendiente de pago`.
- [x] 2.2 Update `subscriptions/tests.py:717` `test_sync_from_stripe_with_listobject_empty_sets_canceled` same assertion for `ListObject(data=[])` variant.
- [x] 2.3 Ensure/keep `ACTIVE + [] → CANCELED` covered (add `test_sync_from_stripe_active_with_no_subscriptions_sets_canceled` if missing — list + ListObject variants).
- [x] 2.4 Run `python manage.py test subscriptions.tests.AdminEndpointTest.test_sync_from_stripe_* subscriptions.tests.StripeCompatTest --verbosity 2` and full `python manage.py test subscriptions --verbosity 1` to confirm no `KeyError`/`AttributeError`/`Decimal` regressions.

## 3. Spec / docs alignment

- [x] 3.1 Verify delta specs `openspec/changes/fix-sync-pending-flap/specs/artist-subscription/spec.md` and `specs/subscription-admin-controls/spec.md` archive correctly (MODIFIED Requirements with full blocks, `#### Scenario:` 4-hash).
- [x] 3.2 Optional follow-up: update `docs/stripe-subscriptions.md:163` note to conditional rule (out-of-scope, leave TODO).

## 4. Manual verification

- [x] 4.1 Create Artist with email, `Generar link` (PENDING), immediately click `Sincronizar desde Stripe` → badge stays `Pendiente de pago` (not `Cancelada definitivamente`), `last_synced_at` advances, `is_active=False` and artist not in `/apis/artworks/artists/`.
- [x] 4.2 Same artist after mocked `invoice.payment_succeeded` / webhook `customer.subscription.created` → `ACTIVE` + visible; then delete subscription in Stripe mock and sync → flips to `CANCELED` + `is_active=False`.

