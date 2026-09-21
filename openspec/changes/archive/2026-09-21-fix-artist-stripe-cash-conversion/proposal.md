## Why

Two bugs in the Artist admin change page (`/admin/artworks/artist/<id>/change/`):

1. **Cash conversion permanently locked after a link is generated.** `_is_online_started()` (`artworks/admin.py`) treats *any* generated Stripe link/customer as "online started", so "Marcar como efectivo" is permanently blocked — even when the artist never paid and the link is dead. Since `marcar_efectivo` is the only thing that would clear the stale `stripe_customer_id`, and it is itself blocked, the artist is stuck on the online path forever.
2. **Link generation breaks permanently when the Stripe customer is deleted/broken.** `generate_link`/`regenerate_link` reuse a stored `stripe_customer_id` with no recovery. A deleted or broken customer makes `create_checkout_session` raise, the generic `except` fails the whole action, and the bad id is never cleared — every retry hits the same dead customer. `open_portal` and `sync_from_stripe` have the same latent failure.

## What Changes

- **Allow cash conversion unless a live Stripe subscription is actually billing.** "Marcar como efectivo" becomes allowed for online rows whose status is `pending`, `canceled`, `canceling`, or `active` with `cancel_at_period_end=True`; it stays blocked only for online `active` (not cancel-requested) and `past_due` rows. This single guard change fixes both the hidden button and the direct-URL refusal.
- **Clear Stripe pointers on cash conversion.** `marcar_efectivo` now also clears `stripe_customer_id` and `stripe_subscription_id` when converting, so cash rows never carry stale Stripe identifiers (aligning with the existing "Cash rows carry no Stripe identifiers" capability).
- **Recover from a deleted/broken Stripe customer in all four Stripe actions.** A shared predicate detects a customer-missing/deleted Stripe error. `generate_link`/`regenerate_link` clear the stale id, create a fresh customer, and retry once; `open_portal`/`sync_from_stripe` clear the stale id and show a targeted Spanish warning ("El customer fue eliminado de Stripe; regenera el link") instead of a generic Stripe-down message.

## Capabilities

### New Capabilities

None.

### Modified Capabilities
- `cash-payments`: the "Mark artist as cash" blocking rule now permits conversion for never-paid / cancel-requested online rows; "Cash rows carry no Stripe identifiers" now has the implementation actually clear the ids on conversion.
- `artist-subscription-actions`: generate/regenerate recover from a missing/deleted Stripe customer (new customer + one retry); open-portal/sync clear the stale id and show a targeted warning instead of the generic Stripe-down error.

## Impact

- `artworks/admin.py` — rework `_is_online_started` (blocking predicate), extend `marcar_efectivo` cleared fields, add stale-customer detection + per-action recovery in `generate_link`, `regenerate_link`, `open_portal`, `sync_from_stripe`.
- `subscriptions/tests.py` — update permission-visibility tests; add tests for allowed/blocked cash conversion, clear-on-convert, and deleted-customer recovery for all four actions.
- No model/migration changes, no dependency changes.