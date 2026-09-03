## Context

`Artist` 1:1 `ArtistSubscription` mirrors Stripe as source of truth. Link generation (`artworks/admin.py:394 generate_link`) creates `PENDING + cus_xxx` with no `sub_xxx`; the subscription only appears after `checkout.session.completed → customer.subscription.created` (`subscriptions/webhooks.py:52/80`). `ArtistAdmin.sync_from_stripe` (`artworks/admin.py:511`) is a manual salvavidas: `fetch_customer` + `list_subscriptions(customer, limit=1)` (`subscriptions/services/stripe_client.py:79`) → `subs.data` (ListObject) vs plain list, `sget/to_plain_dict` for v15 `StripeObject`, then `apply_stripe_payload` or empty→`CANCELED`. Empty is ambiguous (never-subscribed vs deleted). Current code treats both as `CANCELED` (`artworks/admin.py:532-533`), so an early sync flaps `PENDING→CANCELED`. `compute_is_active` (`subscriptions/services/subscription_state.py:16`) is single source for `Artist.is_active`.

Stakeholders: operators using admin, artists on Checkout, public API consumers filtering on `is_active`.

## Goals / Non-Goals

**Goals:**
- Early `sync_from_stripe` on `PENDING` with `[]` keeps `PENDING` and updates `customer_email/last_synced_at` + re-derives `is_active` (still `False`).
- `ACTIVE/PAST_DUE/CANCELING` with `[]` still correctly becomes `CANCELED` (true deletion, per `docs/stripe-subscriptions.md:163`).
- Preserve `ListObject`/blocked-`.get`/`Decimal` handling; no Stripe extra calls; no migration.

**Non-Goals:**
- New gating on `is_active_for_new_signups` or grace period changes.
- Background jobs to re-evaluate `past_due` grace; out-of-scope.
- Changing webhook `customer.subscription.created/updated/deleted` mirroring.
- Passing `currency`/`interval` into sync (price plan unchanged).

## Decisions

- **Guard `status != PENDING` (YAGNI) over `stripe_subscription_id is not None`.**  
  *Why:* Bug is precisely `PENDING` being misclassified; spec status enum is explicit (`artist-subscription` Requirement: status states). `PENDING` is the only state that means "never paid". Checking enum is cheaper, readable, and matches user directive. `stripe_subscription_id` is correlated but `PENDING` rows never have one, so guard is equivalent; enum keeps intent obvious. Alternative `stripe_subscription_id` alone would also fix but hides business rule. Both predicates considered; chosen `status != PENDING` as requested.

- **Keep `customer_email` + `last_synced_at` update even when status unchanged.**  
  *Why:* Sync should still refresh email from `sget(customer,"email")` and timestamp for audit, even if `PENDING`. Otherwise operator sees stale `last_synced_at`. Trade-off: extra `save(update_fields=…)` when `PENDING`; negligible.

- **Reuse `compute_is_active(sub)` after both branches.**  
  *Why:* Single source; `PENDING→is_active=False` consistent, `CANCELED→False`. No branch should bypass it.

- **No raw_state overwrite on empty.**  
  *Why:* Empty means no subscription object to snapshot; keeping previous `raw_state` avoids wiping debug data. Webhook path stores invoice raw_state; sync path stores subscription dict on `apply_stripe_payload`. Empty should not clear.

## Risks / Trade-offs

- [Operator expects `CANCELED` for never-paid pending that they want to abandon] → Mitigation: operator can manually set `CANCELED` via admin or let Checkout expire (`checkout.session.expired` clears link but keeps `PENDING`); no auto-flip needed. Documented in spec delta.
- [Regression if future status added] → Mitigation: Guard is explicit `!= PENDING`; any new pre-payment status must be added to allow-list. Acceptable YAGNI.
- [Tests that asserted old bug] → Mitigation: Update `test_sync_from_stripe_no_subscriptions_sets_canceled` and `test_sync_from_stripe_with_listobject_empty_sets_canceled` to assert `PENDING` stays `PENDING`; keep one `ACTIVE+empty→CANCELED` path covered.
- [Two `save(update_fields)` vs single] → Mitigation: One branch does `apply_stripe_payload` (which saves); empty-PENDING branch does one `save` with `status,customer_email,last_synced_at`. No double-save regression from earlier fix.

## Migration Plan

1. Deploy code change; no data migration.
2. Existing rows already flipped to `CANCELED` erroneously can be re-synced after next payment (webhook will upsert to `ACTIVE`) or operator re-generates link (will reset to `PENDING` on next `generate_link`? Note `generate_link` uses `get_or_create` with `defaults PENDING`; existing row stays `CANCELED` until next `apply_stripe_payload`; operator may need to manually sync after payment). No automated backfill required — low blast radius (only artists who hit early sync).
3. Rollback: revert `artworks/admin.py` guard; no schema to roll back.

## Open Questions

- [Pending → abandoned] Should we expose an explicit "Abandon pending" admin action instead of misusing sync? Ask user (see proposal follow-up).
- Is there any other caller of `list_subscriptions(..., limit=1)` that needs same guard? Only `artworks/admin.py:524`; no other sync path found.
