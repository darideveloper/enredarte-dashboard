---
created: 2026-08-20
updated: 2026-08-20
tags:
  - stripe
  - subscriptions
  - testing
  - documentation
type: guide
status: active
---

# Testing Stripe Subscriptions

This document covers how to configure the Stripe Dashboard, run the local
webhook bridge, and exercise the subscription lifecycle end-to-end against a
test (dev) environment.

## Prerequisites

- Stripe CLI installed and logged in (`stripe login`).
- `.env.dev` with `STRIPE_SECRET_KEY`, `STRIPE_PUBLISHABLE_KEY` and
  `STRIPE_WEBHOOK_SECRET` populated with **test-mode** keys.
- The dashboard running locally (`python manage.py runserver`, port 8000).

## 1. Stripe Dashboard product setup

1. Open the Stripe Dashboard → **Products** → **Add product**.
2. Name it (e.g. "Membresía Enredarte") and add a recurring price
   (`Recurring`) in the plan currency (default `MXN`).
3. Copy the price ID (`price_xxx`) from the price row.
4. In the dashboard admin, open **Suscripciones → Plan de suscripción** and
   paste the `price_xxx` into **ID de precio en Stripe**. Make sure
   **Aceptar nuevas suscripciones** is checked.

## 2. Webhook bridge for local development

Stripe cannot reach `localhost`, so run the Stripe CLI bridge:

```bash
stripe listen --forward-to http://localhost:8000/webhooks/stripe/
```

The CLI prints a `whsec_...` signing secret. Copy it into
`STRIPE_WEBHOOK_SECRET` in `.env.dev` and restart the dev server. The bridge
also prints every event it forwards, which is your live debug log.

> Production: create the endpoint in the Dashboard
> (https://<host>/webhooks/stripe/) and copy the signing secret into
> `STRIPE_WEBHOOK_SECRET`.

## 3. End-to-end test script

Use a staff admin account. Cards: `4242 4242 4242 4242` (success),
`4000 0000 0000 0002` (declined).

### 3.1 Subscribe

1. Create an `Artist` with a real email (`/admin/artworks/artist/add/`).
2. Open the artist change page and click **Generar link de suscripción**.
   - The Checkout URL is copied to the clipboard; share it in an incognito
     browser.
3. Complete checkout with `4242 4242 4242 4242`.
4. Verify:
   - The `stripe listen` log shows `checkout.session.completed` and
     `customer.subscription.created`.
   - `ArtistSubscription.status == "active"` in the admin and
     `Artist.is_active == True`.
   - `/apis/artworks/artists/` includes the artist.

### 3.2 Cancel (friendly cancellation)

1. In the artist change page click **Abrir Customer Portal** and share the
   portal URL, or cancel from the Stripe Dashboard under the customer.
2. The `customer.subscription.updated` event arrives with
   `cancel_at_period_end=true`.
3. Verify `ArtistSubscription.status == "canceling"` and
   `Artist.is_active` is **still True** (visible through period end).
4. When the period ends, `customer.subscription.deleted` arrives.
   Verify `status == "canceled"` and `Artist.is_active == False` — the artist
   disappears from `/apis/artworks/artists/`.

### 3.3 Grace (payment failure)

1. Generate a link, then subscribe using `4000 0000 0000 0002` (declined) —
   or use `stripe trigger invoice.payment_failed`.
2. Verify `invoice.payment_failed` sets `status == "past_due"` while
   `current_period_end + grace_period_days` is in the future: the artist stays
   visible.
3. Wait for the grace window (or shorten `BillingPlan.grace_period_days`) and
   confirm the next event flips `Artist.is_active` to False.

### 3.4 Resume

1. Update the payment method in the Customer Portal to `4242 ...`.
2. Trigger the retry: `stripe trigger invoice.payment_succeeded` (or wait for
   Stripe's automatic retry).
3. Verify `status` returns to `"active"`, `current_period_end` refreshes, and
   `Artist.is_active == True` again.

## 4. Useful CLI triggers

```bash
stripe trigger customer.subscription.created
stripe trigger customer.subscription.updated
stripe trigger customer.subscription.deleted
stripe trigger invoice.payment_succeeded
stripe trigger invoice.payment_failed
stripe trigger checkout.session.completed
```

Each trigger returns 200 if the signature verifies and the handler succeeds.
Every received event appears in **Suscripciones → Eventos de Stripe** (audit
log); failed processing persists the error on the row and Stripe retries.