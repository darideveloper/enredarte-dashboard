## Why

Generating a new payment link creates `ArtistSubscription(status=PENDING, stripe_customer_id=cus_xxx, stripe_subscription_id=None)`. Clicking **Sincronizar desde Stripe** before the artist pays calls `Subscription.list(customer=cus_xxx)` which correctly returns `[]` (`data==[]`) — no subscription exists yet. The current `sync_from_stripe` handler unconditionally interprets empty as `CANCELED` and shows `Suscripción sincronizada: Pendiente de pago → Cancelada definitivamente`, breaking the happy-path and requiring manual correction. Bug was codified by two tests asserting `PENDING → CANCELED` on empty.

## What Changes

- Change `ArtistAdmin.sync_from_stripe` empty-list branch to keep `PENDING` when local `status == PENDING` (YAGNI: `status != PENDING` guard). Only `ACTIVE/PAST_DUE/CANCELING/CANCELED` + `[]` becomes `CANCELED` (true deletion). Always update `customer_email` + `last_synced_at` and re-derive `Artist.is_active` via `compute_is_active`.
- Update / add tests: `PENDING + []` stays `PENDING` (ListObject and plain list variants); `ACTIVE + []` stays `CANCELED`.
- Update spec text `Manual sync with zero subscriptions` to describe conditional rule.
- No model/schema change, no new endpoint.

## Capabilities

### New Capabilities

- _(none)_ — pure behavior fix.

### Modified Capabilities

- `artist-subscription`: Requirement *Operator-controlled sync from Stripe* — scenario `Manual sync with zero subscriptions` changes from unconditional `CANCELED` to conditional (`PENDING` stays `PENDING`).
- `subscription-admin-controls`: Requirement *Sync from Stripe endpoint* — empty-list scenario conditional on prior status.

## Impact

- Code: `artworks/admin.py:531-539` (`sync_from_stripe`), `subscriptions/tests.py` (~2 tests corrected + 1 kept).
- Docs: spec deltas under `artist-subscription` / `subscription-admin-controls`; `docs/stripe-subscriptions.md` clarifies empty case (out-of-scope follow-up).
- Risk: low. No DB migration. Stripe calls unchanged. `compute_is_active(PENDING)` = `False` so public API (`Artist.is_active`) unaffected for pending artists. The only changed path is early sync before first payment; post-payment deletion still flips to `CANCELED`.
