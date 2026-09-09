---
created: 2026-08-26
updated: 2026-08-26
tags:
  - stripe
  - subscriptions
  - setup
  - documentation
type: guide
status: active
---

# Enredarte Stripe Account — Setup Status & Checklist

Current state of the Stripe account setup for the Enredarte dashboard, what
is still pending, and the exact steps to go live.

## Account

- **Account:** Enredarte sandbox (test mode). See account details in the
  Stripe Dashboard (switch to the Enredarte account, test mode).
- The Stripe MCP server (global opencode config `~/.config/opencode/opencode.json`)
  was reconfigured from the DariDevsTeam live key to the Enredarte **test** secret
  key so MCP/CLI operations target this account.

> No secrets belong here. Account, product, price and portal IDs are referenced
> only via the Dashboard; actual values live in gitignored `.env` files.

## Changes already done (test mode)

### Stripe Dashboard / API

1. **Product `Membresía Enredarte`** — active, service type (see Products in the Dashboard, test mode).
2. **Recurring price** — monthly plan price in MXN, set as the product's
   default price (see the price row in the Dashboard).
3. **Customer Portal** — auto-created default configuration (active, default). Features: customer
   update, invoice history, payment method update, cancel at period end.
   No manual configuration needed; `create_billing_portal_session` works.
 4. Webhook signing secret obtained via `stripe listen --print-secret`:
    `whsec_xxxx`
    (no permanent dashboard webhook endpoint exists in test yet — local
   testing uses the CLI bridge).

### Code changes

- `project/settings.py` — added Stripe env vars (`STRIPE_SECRET_KEY`,
  `STRIPE_PUBLISHABLE_KEY`, `STRIPE_WEBHOOK_SECRET`, `STRIPE_API_VERSION`,
  `STRIPE_PRICE_ID` seed, derived `STRIPE_SUCCESS_URL` / `STRIPE_CANCEL_URL` /
  `STRIPE_PORTAL_RETURN_URL`).
- `subscriptions/models.py` — `BillingPlan` is a django-solo singleton with
  admin-editable `amount` / `currency` / `interval`; `stripe_product_id` /
  `stripe_price_id` are auto-managed read-only fields.
- Migrations (latest: `0004_admin_editable_price`) — `STRIPE_PRICE_ID` is only
  an initial seed consumed by the migration via `stripe.Price.retrieve`
  (best-effort); after that the `BillingPlan` row in the DB is the only source
  of truth and no code reads `STRIPE_PRICE_ID` at runtime.
- `.env.dev`, `.env.dev.example`, `.env.prod.example` — added
  `STRIPE_SECRET_KEY`, `STRIPE_PUBLISHABLE_KEY`, `STRIPE_WEBHOOK_SECRET`,
  `STRIPE_API_VERSION` and `STRIPE_PRICE_ID` entries; `.env.dev` populated
  with the test keys + price ID + webhook secret.
- `docs/stripe-subscriptions.md`, `docs/testing-stripe.md` — updated to
  document `STRIPE_PRICE_ID`.

### Verification

- `python manage.py test subscriptions` — 37 tests pass.
- `python manage.py makemigrations --check --dry-run` — no pending changes.
- Portal session creation tested end-to-end (test customer + `billing_portal
  sessions create`) and returned a valid URL; test customer then deleted.
- Test card: `4242 4242 4242 4242` (success), `4000 0000 0000 0002` (declined).

## Pending changes (test mode)

1. **Run the local end-to-end flow** (docs/testing-stripe.md §3):
   - Start the dev server and, in another terminal:
     `stripe listen --forward-to http://localhost:8000/webhooks/stripe/ --api-key <sk_test_...>`
   - Create an `Artist` with a real email in the admin.
   - Click **Generar link de suscripción**, complete checkout with the test
     card, and verify webhook events + `Artist.is_active` flips.
2. If a permanent test webhook endpoint in the Dashboard is wanted (instead of
   the CLI bridge), create it at `https://<host>/webhooks/stripe/` with
   `STRIPE_API_VERSION` (`2026-07-29.dahlia`) and events:
   `checkout.session.completed`, `customer.subscription.created/updated/deleted`,
   `invoice.payment_succeeded`, `invoice.payment_failed`. Copy the `whsec_...`
   into `STRIPE_WEBHOOK_SECRET`.
3. Confirm the exact membership amount/currency is correct
   (edited from the admin: **Suscripciones → Plan de suscripción** —
   Monto/Moneda; the price is dynamic and may change).
4. Apply pending migrations to the dev database
   (`python manage.py migrate`), which is reachable only with the dev DB
   credentials.

## Production / live mode checklist

Same Stripe account, switch to live keys. Product/prices/portal must be
**created again in live mode** — Stripe test and live are fully separate.

1. **Live keys**
   - Dashboard → **Developers → API keys**: copy `pk_live_...` and `sk_live_...`.
   - Set in the production environment (`.env.prod` / deploy secrets):
     `STRIPE_SECRET_KEY=sk_live_...`, `STRIPE_PUBLISHABLE_KEY=pk_live_...`.

2. **Create the live product + price**
   - In live mode, add the product **Membresía Enredarte** with a recurring
     monthly price (confirm amount/currency in the admin form — the price is
     dynamic and managed from **Suscripciones → Plan de suscripción**).
   - Saving the plan in the admin creates the live `price_...` under the same
     product and archives the previous one. `STRIPE_PRICE_ID` is only an
     initial seed for fresh databases, not the runtime source of truth.
   - Verify `BillingPlan.is_active_for_new_signups = True`.

3. **Webhook endpoint (live)**
   - Dashboard → **Developers → Webhooks → Add endpoint**:
     `https://<host>/webhooks/stripe/` (HTTPS, public).
   - API version: match `STRIPE_API_VERSION` (`2026-07-29.dahlia`).
   - Events (same set as test):
     `checkout.session.completed`,
     `customer.subscription.created`, `customer.subscription.updated`,
     `customer.subscription.deleted`,
     `invoice.payment_succeeded`, `invoice.payment_failed`.
   - Copy the signing secret into `STRIPE_WEBHOOK_SECRET` in production.
   - Stripe retries failed deliveries; the endpoint is idempotent via the
     unique `StripeEvent.event_id` and returns 500 on handler errors so
     Stripe retries.

4. **Customer Portal (live)**
   - Confirm the portal configuration exists in live mode (auto-created on
     first portal session, or configure in Dashboard → **Settings → Billing →
     Customer portal**). The default supports cancel at period end, invoice
     history and payment method update, which matches the project flow.

5. **URLs (live)**
   - `HOST` must be the real production domain. `STRIPE_SUCCESS_URL` /
     `STRIPE_CANCEL_URL` default to `{HOST}/subscriptions/success/` and
     `/subscriptions/cancel/`; `STRIPE_PORTAL_RETURN_URL` is
     `{HOST}/subscriptions/portal-return/` (neutral landing). Verify these
     routes are deployed and reachable.

6. **Deploy + migrate**
   - Deploy the app with the live env vars, run
     `python manage.py migrate` (applies up to `0004_admin_editable_price`).
   - Note: the seed migration only backfills when `STRIPE_PRICE_ID` is set in
     the environment at migrate time; for a fresh production DB the admin
     form creates the price on first save.

7. **End-to-end smoke test in live**
   - Create a test `Artist`, generate the link, pay with a real (or a live
     test) card in a sandbox checkout, and confirm webhooks update
     `ArtistSubscription` + `Artist.is_active`, and the artist appears in
     `/api/artworks/artists/`.

8. **Security / hygiene**
   - Never commit live keys. `.env*` files are gitignored; keep live values
     in the deploy secrets manager.
   - If the MCP/CLI are used for live ops, re-point the global Stripe MCP key
     to the live secret only for the operation, then revert to avoid
     accidental live changes.

## Useful CLI triggers (test)

```bash
stripe trigger customer.subscription.created
stripe trigger customer.subscription.updated
stripe trigger customer.subscription.deleted
stripe trigger invoice.payment_succeeded
stripe trigger invoice.payment_failed
stripe trigger checkout.session.completed
```