---
created: 2026-08-20
updated: 2026-08-29
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

## Step-by-Step Subscription Flow

### 1. Setup Phase
1. **Operator creates an Artist** in Django admin with a required email address
2. **Configure BillingPlan** singleton (django-solo) with:
   - Stripe price ID (`price_xxx`)
   - Currency (default: MXN)
   - Grace period (default: 3 days)
   - "Accept new signups" toggle

### 2. Payment Link Generation
1. Operator clicks **"Generar link de suscripción"** on the Artist change page
2. System creates:
   - Stripe Customer (if not exists)
   - Stripe Checkout Session with `metadata.artist_id`
   - `ArtistSubscription(status="pending", signup_url="...")`
3. Once the link exists, a **"Copiar link"** button appears on the change page;
   the operator clicks it to copy the Checkout URL to the clipboard and share
   it via email/WhatsApp

### 3. Artist Payment
1. Artist opens Checkout Session URL in incognito browser
2. Completes payment (card: `4242 4242 4242 4242` for testing)
3. Stripe sends `checkout.session.completed` webhook

### 4. Webhook Processing
Webhook endpoint `POST /webhooks/stripe/` processes events:
1. **Signature verification** using `stripe.Webhook.construct_event`
2. **Idempotency** via `StripeEvent.event_id` unique constraint
3. **Atomic transaction** updates both:
   - `ArtistSubscription.status` (mirrors Stripe state)
   - `Artist.is_active` (via `compute_is_active()` helper)

### 5. Subscription States & Visibility

| Subscription Status | `Artist.is_active` | Behavior |
|---------------------|-------------------|----------|
| `active` | `True` | Artist visible on public site |
| `pending` | `False` | Unpaid link does NOT make artist visible |
| `canceling` | `True` until period end | Friendly cancellation - visible until paid period ends |
| `past_due` | `True` for 3 days grace | Payment failed but within grace period |
| `canceled` | `False` | Artist disappears from public site |

### 6. Admin Controls
From the Artist change page, the header buttons depend on the subscription state:

| State                        | Buttons shown |
|------------------------------|---------------|
| No link (no subscription / empty `signup_url`) | **Generar link**, Sincronizar desde Stripe |
| Expired link                 | **Regenerar link**, Abrir Customer Portal, Sincronizar desde Stripe |
| Valid (non-expired) link     | **Copiar link**, Regenerar link, Abrir Customer Portal, Sincronizar desde Stripe |

- **Generar / Regenerar link** - Create new Checkout Session
- **Copiar link** - Client-side button that copies the preloaded `signup_url` to the clipboard on click
- **Abrir Customer Portal** - Stripe-hosted self-service (cancel, update card, invoices)
- **Sincronizar desde Stripe** - Manual state re-sync escape hatch

### 7. Public API
`/apis/artworks/artists/` filters on `Artist.is_active` - unchanged API, only the driver of `is_active` changes.

## Editar el precio desde el admin

El precio de la suscripción se edita desde **Suscripciones → Plan de suscripción** con tres campos amigables: **Monto** (decimal > 0), **Moneda** (MXN / USD) y **Periodicidad** (actualmente solo `month`). El operador nunca escribe un `price_xxx` manualmente.

- **Campos auto-gestionados (solo lectura):** `stripe_product_id`, `stripe_price_id` y `last_synced_stripe_at`. Se rellenan automáticamente al guardar. La UI muestra una línea de solo lectura **"Confirmado por Stripe"** que hace `stripe.Price.retrieve(stripe_price_id)` al cargar el formulario (GET) para verificar que la DB coincide con Stripe.
- **Semilla inicial `STRIPE_PRICE_ID`:** la variable de entorno solo se usa una vez, en la migración `0004`, para poblar `amount`/`currency`/`interval`/`stripe_product_id`/`stripe_price_id` vía `stripe.Price.retrieve` (best-effort). Si no está configurada o Stripe no responde, `amount` queda en `0` y el operador debe guardar el formulario una vez. Después de la migración, el `BillingPlan` en la DB es la única fuente de verdad; ningún código lee `STRIPE_PRICE_ID` en tiempo de ejecución.
- **Qué pasa con suscriptores existentes:** cambiar el precio crea un nuevo `price_xxx` bajo el mismo producto y archiva el anterior. Las suscripciones ya activas siguen facturándose al precio antiguo (comportamiento estándar de Stripe: archivar un precio no afecta suscripciones existentes). Solo las nuevas altas usan el precio nuevo. Documentado como callout principal para evitar sorpresas.
- **Auditoría:** cada cambio exitoso crea una fila en `BillingPlanPriceHistory` (`old_stripe_price_id` → `new_stripe_price_id`, `amount`/`currency`/`interval`, `old_price_archived`, `changed_by`, `changed_at`). Visible como inline de solo lectura en el cambio de `BillingPlan`, ordenado por `-changed_at`.

### Old-price archival

En cada cambio que crea un nuevo precio, el `price_xxx` anterior se archiva en Stripe con `stripe.Price.modify(old_id, active=False)` de modo que no pueda reutilizarse para nuevos checkouts. Si no había precio previo (primera creación), no se archiva nada y `old_stripe_price_id=""` en el historial.

## The `compute_is_active` rule

`subscriptions/services/subscription_state.compute_is_active(subscription)` is
the **single source of truth** for `Artist.is_active`. No webhook handler or
admin action derives the boolean inline.

| Subscription status            | `Artist.is_active`                          |
|--------------------------------|---------------------------------------------|
| `active`                       | `True`                                      |
| `pending`                      | `False` (unpaid link does NOT make the artist visible) |
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

- **Generar link de suscripción** — shown only when no link exists. Creates a
  Stripe Customer + Checkout Session, stores the `signup_url`, and marks the
  subscription `pending`.
- **Copiar link** — a client-side `<button>` (rendered through Unfold's button
  component) with the `signup_url` preloaded in `data-copy-url`; clicking it
  copies the URL via the Clipboard API (no server round-trip, no cookie).
- **Regenerar link** — shown when a link exists (valid or expired). Reuses a
  still-valid Checkout Session or creates a fresh one when expired.
- **Abrir Customer Portal** — Stripe-hosted self-service page for the artist
  (update card, cancel, invoices). Its `return_url` points at the neutral
  landing page `/subscriptions/portal-return/` (generic message) so an artist
  who just cancelled does not land on the "subscription active" success text.
- **Sincronizar desde Stripe** — manual salvavidas: re-fetches customer and
  latest subscription from the API and re-derives `is_active`. When the
  customer exists but has **zero subscriptions** (all deleted), the local
  status is set to `canceled` — the artist holds no paying subscription and
  stops appearing on the public site.

All of these are Unfold `actions_detail` buttons on the change-form header,
gated by `admin.site.admin_view` (redirect to admin login for anonymous users,
forbidden for non-staff).

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
  `STRIPE_API_VERSION`, `STRIPE_PRICE_ID`
- Derived: `STRIPE_SUCCESS_URL` / `STRIPE_CANCEL_URL` (from `HOST`, defaulting
  to `/subscriptions/success/` and `/subscriptions/cancel/`).

## Deployment notes

- Configure the production webhook endpoint at
  `https://<host>/webhooks/stripe/` and set `STRIPE_WEBHOOK_SECRET`.
- Until `BillingPlan.stripe_price_id` is set, link generation refuses with an
  admin message and existing `Artist.is_active=True` behavior is unchanged.
  `STRIPE_PRICE_ID` solo se usa como semilla inicial en la migración `0004`; después el admin es la fuente de verdad (ver "Editar el precio desde el admin").
- The migration that makes `Artist.email` required backfills existing rows with
  `""` and prints a console warning listing affected artists for follow-up.

## Testing

### Prerequisites
1. Install Stripe CLI and login: `stripe login`
2. Configure `.env.dev` with test-mode keys:
   - `STRIPE_SECRET_KEY` (test `sk_test_...`)
   - `STRIPE_PUBLISHABLE_KEY` (test `pk_test_...`)
   - `STRIPE_PRICE_ID` (from Stripe Dashboard)
3. Start webhook bridge:
   ```bash
   stripe listen --forward-to http://localhost:8000/webhooks/stripe/
   ```
4. Copy `whsec_...` from CLI output to `STRIPE_WEBHOOK_SECRET` in `.env.dev`
5. Start dev server: `python manage.py runserver`

### Test Flow

#### Subscribe (Happy Path)
1. Create Artist with real email in admin
2. Click **Generar link de suscripción**
3. Open Checkout URL in incognito, pay with `4242 4242 4242 4242`
4. Verify:
   - `stripe listen` shows `checkout.session.completed` + `customer.subscription.created`
   - `ArtistSubscription.status == "active"`
   - `Artist.is_active == True`
   - Artist appears in `/apis/artworks/artists/`

#### Cancel (Friendly Cancellation)
1. Click **Abrir Customer Portal** → cancel subscription
2. `customer.subscription.updated` arrives with `cancel_at_period_end=true`
3. Verify `status == "canceling"` and `is_active == True` (still visible)
4. When period ends, `customer.subscription.deleted` arrives
5. Verify `status == "canceled"` and `is_active == False` (artist disappears)

#### Payment Failure (Grace Period)
1. Subscribe with `4000 0000 0000 0002` (declined card)
2. Verify `status == "past_due"` and artist stays visible for 3 days
3. After grace period, next event flips `is_active` to `False`

#### Resume
1. Update payment method in Customer Portal to `4242...`
2. Trigger retry: `stripe trigger invoice.payment_succeeded`
3. Verify `status == "active"` and `is_active == True` again

### Useful CLI Triggers
```bash
stripe trigger customer.subscription.created
stripe trigger customer.subscription.updated
stripe trigger customer.subscription.deleted
stripe trigger invoice.payment_succeeded
stripe trigger invoice.payment_failed
stripe trigger checkout.session.completed
```

All received events appear in **Suscripciones → Eventos de Stripe** audit log.
