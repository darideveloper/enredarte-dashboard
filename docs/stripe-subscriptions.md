---
created: 2026-08-20
updated: 2026-08-20
tags:
  - stripe
  - subscriptions
  - architecture
  - documentation
type: resource
status: active
---

# Stripe Artist Subscriptions — Architecture

How paid membership gating works in the Enredarte dashboard.

## Overview

Each `Artist` has at most one `ArtistSubscription` (1:1). Stripe is the source
of truth for the subscription lifecycle; the dashboard mirrors the minimal
state it needs and derives `Artist.is_active` from it. The public API
(`/apis/artworks/artists/`) keeps filtering on `Artist.is_active` — it does not
know about subscriptions at all.

Layers:

```
stripe SDK  ──► subscriptions/services/stripe_client.py   (only file that imports `stripe`)
webhooks / views  ──► services/subscription_state.compute_is_active()
ArtistSubscription / StripeEvent  (subscriptions/models.py)
ArtistAdmin buttons (artworks/admin.py + change_form template)
```

## The `compute_is_active` rule

`subscriptions/services/subscription_state.compute_is_active(subscription)` is
the **single source of truth** for `Artist.is_active`. No webhook handler or
admin action derives the boolean inline.

| Subscription status            | `Artist.is_active`                          |
|--------------------------------|---------------------------------------------|
| `pending` / `active`           | `True`                                      |
| `canceling`                    | `True` until `current_period_end`           |
| `past_due`                     | `True` until `current_period_end + grace`   |
| `canceled`                     | `False`                                     |
| no subscription row            | artist's current value, untouched           |

`grace_period_days` comes from the `BillingPlan` singleton. The grace boundary
is re-evaluated on every webhook that touches the row (there is no background
job in v1); the next event that crosses the boundary performs the flip.

## Webhook idempotency model

`POST /webhooks/stripe/` is the only endpoint outside the admin; its security
boundary is the `Stripe-Signature` header (`stripe.Webhook.construct_event`,
`@csrf_exempt`).

1. The event is INSERTed into `StripeEvent` inside its own savepoint, keyed by
   the unique `event_id`. A duplicate INSERT raises `IntegrityError` and the
   endpoint returns `200` immediately — **no** side effects (the unique index
   is the lock; the savepoint keeps an enclosing transaction healthy).
2. Handled events run inside one `transaction.atomic()` block:
   `ArtistSubscription` mirror + `Artist.is_active` commit together.
3. If the handler raises, the transaction rolls back, the `error` is persisted
   on the `StripeEvent` row **outside** the atomic block, and the endpoint
   returns `500` so Stripe retries.

Dispatch table: `checkout.session.completed`,
`customer.subscription.created/updated/deleted`, `invoice.payment_succeeded`,
`invoice.payment_failed`. Unhandled event types are still recorded and return
`200`.

Correlation is by `stripe_subscription_id` first, then `stripe_customer_id`;
`checkout.session.completed` correlates via `metadata.artist_id` (set on the
Checkout Session) before the customer id is stored locally.

## Admin controls

From the `Artist` change page the operator can:

- **Generar / Regenerar link de suscripción** — creates a Stripe Customer +
  Checkout Session (`subscriptions:generate-link` / `regenerate-link`), stores
  the `signup_url`, and sets a `copy_to_clipboard` cookie (the existing
  `static/js/copy_clipboard.js` copies it on next page load).
- **Abrir Customer Portal** — Stripe-hosted self-service page for the artist
  (update card, cancel, invoices). Its `return_url` points at the neutral
  landing page `/subscriptions/portal-return/` (generic message) so an artist
  who just cancelled does not land on the "subscription active" success text.
- **Sincronizar desde Stripe** — manual salvavidas: re-fetches customer and
  latest subscription from the API and re-derives `is_active`. When the
  customer exists but has **zero subscriptions** (all deleted), the local
  status is set to `canceled` — the artist holds no paying subscription and
  stops appearing on the public site.

All four endpoints are `POST`-only and gated by `admin.site.admin_view`
(redirect to admin login for anonymous users, forbidden for non-staff).

## Adding more billing plans later (without breaking the migration)

Today there is exactly one canonical plan (`BillingPlan` django-solo singleton)
used unconditionally — there is no "select plan" dropdown anywhere. To support
tiers later:

1. Keep `BillingPlan` for the default/legacy plan or migrate it to a plain
   model; the `ArtistSubscription.artist` 1:1 **does not change**, so no
   subscription rows are affected.
2. Add an optional `plan` FK to `ArtistSubscription` (nullable) and create
   extra `BillingPlan` rows. Existing rows keep pointing at the default plan.
3. Make the link-generation endpoints read the plan from the artist
   (e.g. a future `plan` FK on `Artist`), passing its `stripe_price_id` to
   `stripe_client.create_checkout_session`.
4. `compute_is_active` stays unchanged — grace comes from each row's own plan
   (`subscription.plan.grace_period_days`) instead of `BillingPlan.get_solo()`.

This keeps the migration additive (new nullable column), never requiring a
data rewrite of existing subscriptions.

## Environment variables

- `STRIPE_SECRET_KEY`, `STRIPE_PUBLISHABLE_KEY`, `STRIPE_WEBHOOK_SECRET`,
  `STRIPE_API_VERSION`
- Derived: `STRIPE_SUCCESS_URL` / `STRIPE_CANCEL_URL` (from `HOST`, defaulting
  to `/subscriptions/success/` and `/subscriptions/cancel/`).

## Deployment notes

- Configure the production webhook endpoint at
  `https://<host>/webhooks/stripe/` and set `STRIPE_WEBHOOK_SECRET`.
- Until `BillingPlan.stripe_price_id` is set, link generation refuses with an
  admin message and existing `Artist.is_active=True` behavior is unchanged.
- The migration that makes `Artist.email` required backfills existing rows with
  `""` and prints a console warning listing affected artists for follow-up.