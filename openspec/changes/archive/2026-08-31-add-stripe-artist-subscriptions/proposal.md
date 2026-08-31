# Add Stripe Artist Subscriptions

## Why

The Enredarte public site lists artists, but today there is no commercial gate: any artist an operator creates in the dashboard appears immediately on `/apis/artworks/artists/`. We need a paid membership so that appearing on the site is conditional on an active subscription, with automatic deactivation when the subscription lapses and automatic reactivation when payment resumes. Operators also need to be able to create, regenerate, and share a payment link for any artist from the Django Unfold admin, and to see subscription state in real time.

## What Changes

- New Django app `subscriptions` registered in `INSTALLED_APPS`.
- New `BillingPlan` (django-solo) singleton edited in admin: `stripe_price_id`, `currency` (default `MXN`), `grace_period_days` (default `3`), `is_active_for_new_signups`.
- New `ArtistSubscription` model (1:1 with `Artist`) mirroring the minimum needed Stripe state: `status`, `stripe_customer_id`, `stripe_subscription_id`, `current_period_end`, `cancel_at_period_end`, `customer_email`, `signup_url`, `signup_url_expires_at`, `last_synced_at`, `raw_state`.
- New `StripeEvent` audit-log model: every received webhook is recorded with `event_id`, `event_type`, `payload`, `processed_at`, `error` for idempotency and debugging.
- `Artist.email` becomes required (`null=False`) — Stripe needs it as customer identifier once an operator triggers a subscription link.
- `Artist.is_active` becomes driven by `ArtistSubscription.status` through a single helper `subscription_state.compute_is_active(subscription)`; the helper is the only place that decides the boolean, called from webhook handlers inside `transaction.atomic()`. An artist is visible on the public site only once their subscription is `active` (or inside the grace / friendly-cancellation windows); a generated-but-unpaid `pending` link does NOT make the artist visible.
- New endpoints:
  - `POST /subscriptions/admin/artists/<id>/generate-link/` — create Stripe Customer + Checkout Session, persist `ArtistSubscription(status=PENDING, signup_url)`.
  - `POST /subscriptions/admin/artists/<id>/regenerate-link/` — same, replaces `signup_url` if expired.
  - `POST /subscriptions/admin/artists/<id>/open-portal/` — returns a Stripe Customer Portal session URL.
  - `POST /subscriptions/admin/artists/<id>/sync-from-stripe/` — re-fetches the customer/subscription from Stripe API as a manual salvavidas.
  - `GET /subscriptions/success/?session_id=...` — landing page after a successful checkout.
  - `GET /subscriptions/cancel/` — landing page after a cancelled checkout.
  - `GET /subscriptions/portal-return/` — neutral landing page where the artist lands after leaving the Stripe Customer Portal (kept generic: card updated, invoice viewed, or cancelled).
  - `POST /webhooks/stripe/` — Stripe-signed webhook receiver; signature verified with `stripe.Webhook.construct_event`; idempotent via `StripeEvent.event_id` unique field; processes the event inside a transaction and updates `Artist.is_active`.
- `ArtistAdmin` (in `artworks/admin.py`) gains a "Suscripción" badge column on the changelist and admin actions on the edit view: "Generar / Regenerar link de pago", "Abrir Customer Portal", "Sincronizar desde Stripe".
- New `stripe` dependency added to `requirements.txt`. Environment variables: `STRIPE_SECRET_KEY`, `STRIPE_PUBLISHABLE_KEY`, `STRIPE_WEBHOOK_SECRET`, `STRIPE_API_VERSION`.
- New `subscriptions/services/stripe_client.py` wraps the `stripe` SDK so the call sites use only our small surface area.
- Locale strings added for subscription-related admin labels in `es` and `en`.

## Capabilities

### New Capabilities

- `billing-plan`: `BillingPlan` singleton editable in admin; defines the unique Stripe price, currency, grace period and whether new sign-ups are accepted. One canonical plan today; architected so additional `Plan` rows can be added later without breaking the 1:1 `Artist` → `ArtistSubscription` mapping.
- `artist-subscription`: `ArtistSubscription` lifecycle managed by Stripe webhooks — operator creates an `Artist`, generates a Checkout Session link, the artist pays, Stripe sends `customer.subscription.created`, the subscription mirrors to `status=ACTIVE`. Cancellation, payment failures and reactivation all flow through the same webhook pipeline with idempotency and transactional state updates to `Artist.is_active`.
- `stripe-webhook-handler`: Stripe events arrive over a signed POST endpoint, are persisted to `StripeEvent` for audit + idempotency, and dispatched to one handler per event type. All handlers run inside `transaction.atomic()` and call the same `subscription_state.compute_is_active(subscription)` helper to keep `Artist.is_active` consistent.
- `subscription-admin-controls`: from `ArtistAdmin` (and from the `ArtistSubscription` admin when relevant) the operator can generate / regenerate the Checkout Session link, open the Stripe-hosted Customer Portal for an artist (to manage payment method, view invoices, cancel), re-sync a single artist's state from Stripe, and inspect the full webhook audit log.

### Modified Capabilities

- `artist-admin`: `ArtistAdmin` changelist adds a "Suscripción" status column; the change view gains subscription action buttons. Field `Artist.email` becomes required.
- `artworks-rest-api`: unchanged. The existing `is_active=True` filter remains the source of truth; only the underlying driver of `is_active` shifts to include subscription state. No spec-level requirement changes, so no delta is produced for this capability.

## Impact

- New code under `subscriptions/` (`models.py`, `services/`, `webhooks.py`, `views.py`, `urls.py`, `apps.py`, `admin.py`, migrations).
- Edits to `artworks/models.py` (email required), `artworks/admin.py` (subscription column + action buttons), `artworks/views.py` (no functional change — `is_active` still drives filtering).
- Edits to `project/settings.py` (register app, read Stripe env vars, webhook URL config).
- Edits to `project/urls.py` (mount `subscriptions.urls` and the webhook endpoint).
- Edits to `requirements.txt` (add `stripe`).
- Edits to `.env.dev.example` and `.env.prod.example` (Stripe credentials).
- New locale strings for `es` and `en` for subscription admin labels.
- New Stripe product + price must be configured in the Stripe Dashboard out-of-band (out of this change's automation scope).
- Webhook testing in development requires `stripe listen --forward-to ...` (Stripe CLI; existing `requests` dep is sufficient).
