## Why

Operators cannot filter or visually distinguish artists paying via Stripe (`payment_method=online`) from artists paying manually (`payment_method=cash`) in the Artist changelist. The `Suscripción` badge shows only `status`, so a cash-`active` and a Stripe-`active` look identical, and neither the Artist nor the Subscription changelist offers a payment-method filter. This slows down daily cash workflows (confirm pending cash, find cash artists) and risks applying Stripe actions to cash rows.

## What Changes

- Add `ArtistPaymentMethodFilter` (`En línea` / `Efectivo` / `Sin suscripción`) to `ArtistAdmin.list_filter`, placed **first (top)** per operator request, implemented with `Exists`/`OuterRef` subqueries (same pattern as `ArtistAvailableWorksFilter`).
- Enrich the existing `Suscripción` badge to prefix the payment method (`Efectivo · Activa` / `En línea · Activa`), keeping current status colors; `Sin suscripción` stays muted. Backed by a new `_payment_method` `Subquery` annotation in `ArtistAdmin.get_queryset` (no per-row queries).
- Add plain `payment_method` to `ArtistSubscriptionAdmin.list_filter` for consistency (direct field filter, no subquery needed).
- No model/migration changes; no new columns; no status semantics change.

## Capabilities

### New Capabilities

- `artist-payment-method-filter`: filter artists by subscription payment method and identify the method at a glance via the enriched badge.

### Modified Capabilities

- `artist-admin`: `ArtistAdmin` changelist gains the payment-method filter (top position) and the `Suscripción` badge label now includes the payment method.
- `admin-list-performance`: the new filter MUST use `Exists` subqueries and the badge MUST render from annotations (no per-row queries), extending the existing no-N+1 contract.
- `subscription-admin-controls`: `ArtistSubscriptionAdmin` changelist gains a `payment_method` filter alongside the existing `status` filter.

## Impact

- Code: `artworks/admin.py` (new filter class + `list_filter` entry + `_payment_method` annotation), `subscriptions/admin_helpers.py` (badge prefix), `subscriptions/admin.py` (one-line `list_filter` addition), `artworks/tests.py` / `subscriptions/tests.py` (filter + badge tests).
- No DB migration, no API/dependency changes, no Stripe behavior change.
- Risk: low — read-only changelist rendering; cash/online state machine untouched.
