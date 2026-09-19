## Why

Some artists cannot or will not pay online via Stripe (no card, cash-only preference). Today the dashboard offers only the Stripe path: `ArtistSubscription` mirrors Stripe state and every admin control generates a Checkout link. Operators have no supported way to onboard cash payers, so they either force Stripe or track cash outside the platform with no audit trail and no visibility gating.

## What Changes

- Add `ArtistSubscription.payment_method` (`online` | `cash`, default `online`) as the discriminator between Stripe-tracked and manually-managed subscriptions.
- Add three admin cash actions on the Artist change page (Unfold `actions_detail` header buttons, same pattern as Stripe buttons):
  - **Marcar como efectivo** — registers a cash subscription (`pending`, hidden).
  - **Confirmar pago** — confirms cash payment (`active`, visible, indefinite until cancelled).
  - **Cancelar efectivo** — cancels cash (`canceled`, hidden).
- Gate button visibility by payment path: Stripe buttons (`Generar/Regenerar link`, `Abrir Customer Portal`, `Sincronizar desde Stripe`, `Copiar link`) show only for online rows; cash buttons show only for cash-eligible states. Server-side guards refuse cross-path execution via direct URL.
- Guard Stripe write-paths against cash rows: webhooks (`upsert_from_stripe` correlation) log + ignore cash rows; `sync_from_stripe` / `open_portal` refuse cash rows with an admin message.
- Build the project's first email infrastructure (none exists today — no `EMAIL_*` in settings/env, zero mail sends):
  - `EMAIL_*` settings + per-environment env vars; console backend in dev/test, SMTP in prod; `EMAILS_NOTIFICATIONS` recipient list.
  - Central `subscriptions/services/notifications.py` mailer (single mail-sending module) with paired HTML+TXT templates per cash transition.
  - Fire artist receipt + admin notice on **all three** cash transitions (pending, active, canceled). Email failure never rolls back the state change (log + warning message).
- Reuse `Status.pending/active/canceled` + existing `compute_is_active()` for cash (no new status values, no badge/API changes). Cash validity is indefinite until cancelled — no expiry job, no grace window.

## Capabilities

### New Capabilities
- `cash-payments`: manual cash subscription lifecycle (payment_method discriminator, three admin transitions, indefinite validity, Stripe-path isolation).
- `email-notifications`: project email infrastructure (SMTP/console settings, central mailer service, HTML+TXT template convention, cash transition emails to artist + admin list).

### Modified Capabilities
- `artist-subscription`: `ArtistSubscription` gains `payment_method`; cash rows reuse existing statuses with manual (non-Stripe) provenance.
- `artist-subscription-actions`: Artist header button set becomes payment-path aware (Stripe vs cash visibility + cross-path refusal).
- `stripe-webhook-handler`: webhook correlation and manual sync/portal flows must ignore or refuse cash rows instead of mirroring Stripe state onto them.

## Impact

- Affected code: `subscriptions/models.py` (new field + migration), `artworks/admin.py` (3 new actions + 4 modified permission guards), `subscriptions/webhooks.py` + `subscriptions/models.py::upsert_from_stripe` (cash guards), `project/settings.py` + `.env.*(.example)` (EMAIL block), new `subscriptions/services/notifications.py` + 12 email templates (artist + admin pair per transition).
- No API changes: public `/api/artworks/artists/` still filters on `Artist.is_active` only.
- No new dependencies (Django stdlib `django.core.mail` only).
- No breaking changes: existing online rows default to `payment_method=online`, Stripe behavior unchanged.
