## Why

Artwork sales (`ArtworkOrder` lifecycle) are modeled in `artworks/` but all of their Stripe plumbing lives in `subscriptions/`: payment-mode Checkout creation, sale emails + templates, and artwork webhook branches. Every sale request therefore imports from `subscriptions`, and the `subscriptions` webhook lazily imports from `artworks`, hiding the real ownership and making future payment work (second PSP, refunds policy) land in the wrong app. Fix now while the mapping is fully inventoried and before more sale features accrete.

## What Changes

- Move sale Stripe client functions (`create_artwork_checkout_session`, `retrieve_checkout_session`, `create_refund`) from `subscriptions/services/stripe_client.py` to flat module `artworks/stripe_orders.py`. Subscription-mode functions stay. (`artworks/services.py` already exists as a file, so new modules are flat siblings, not a `services/` package.)
- Move sale email senders (`_SALE_*`, `_send_sale`, `send_sale_*`, `_sale_context`, `artwork_artist_email`) from `subscriptions/services/notifications.py` to flat module `artworks/sale_notifications.py`. Cash + online senders stay. The shared mail plumbing (`send_best_effort`, per-audience renderer) moves to `core/mail_utils.py` with the renderer **parameterized to take a full template base path** (today it hardcodes `subscriptions/email/`), so sale sends resolve `artworks/email/sale_*` and online sends keep resolving `subscriptions/email/*`.
- Move 36 `sale_*` email templates from `subscriptions/templates/subscriptions/email/` to `artworks/templates/artworks/email/` (same basenames, TXT+HTML pairs preserved).
- Move artwork webhook branches from `subscriptions/webhooks.py` into flat module `artworks/order_webhooks.py` as pure logic; `subscriptions/webhooks.py` keeps the signed envelope + `StripeEvent` idempotency insert and dispatches by `metadata.kind == "artwork_order"`. **No URL change**: single `POST /webhooks/stripe/` preserved.
- Add `core/stripe.py`: the single import-time Stripe SDK initializer (`stripe.api_key`, `stripe.api_version`) + `STRIPE_*` presence check. Both `artworks/stripe_orders.py` and `subscriptions/services/stripe_client.py` import it, so artwork-only paths (`sync_orders_from_stripe`, `buy`) can never call Stripe unauthenticated.
- Move shared primitives `StripeEvent` + `epoch_to_datetime` from `subscriptions/models.py` to `core/` (no new app): `core/models.py` (`StripeEvent`) + `core/stripe_utils.py` (`epoch_to_datetime`); `subscriptions/services/stripe_compat.py` (`sget`/`to_plain_dict`) moves to `core/stripe_compat.py` with all import sites updated and the old module deleted. Data migration preserves all rows.
- **Scope rule:** `artworks/` sale modules (`stripe_orders.py`, `sale_notifications.py`, `order_webhooks.py`, sale paths in `views.py`/`services.py`/commands) SHALL NOT import from `subscriptions`. `artworks/admin.py` SHALL continue to import subscription-domain services for **artist-membership** admin (generate link, portal, cash, sync) — that is legitimate cross-domain use, explicitly out of scope.
- **BREAKING** (internal only, hard cut, no compat shims): all internal imports, ~43 test mock paths (`subscriptions.services.stripe_client.create_artwork_*` → `artworks.stripe_orders.*`, `subscriptions.services.notifications.send_sale_*` → `artworks.sale_notifications.*`), template names (`subscriptions/email/sale_*` → `artworks/email/sale_*`), and `subscriptions.models.StripeEvent` → `core.models.StripeEvent` change at once. No public API, URL, subject-line, or lifecycle change.

## Capabilities

### New Capabilities

- `shared-stripe-primitives`: shared Stripe audit, helpers, and SDK initialization owned by `core/` (`StripeEvent` idempotency log, `epoch_to_datetime`, `sget`/`to_plain_dict`, `core/stripe.py` credential init), importable by both `subscriptions` and `artworks` with zero domain coupling.

### Modified Capabilities

- `artwork-sales`: Stripe Checkout creation/verification/refund import paths move to flat `artworks/stripe_orders.py`; lifecycle behavior unchanged.
- `sales-emails`: sender module moves to flat `artworks/sale_notifications.py` and template path moves to `artworks/email/sale_*`; subjects, audiences, best-effort contract unchanged.
- `stripe-webhook-handler`: artwork branches become delegated `artworks/order_webhooks.py` logic behind the same envelope + dispatch; signature, idempotency, atomicity, and single-URL behavior unchanged.
- `email-notifications`: "only module that sends mail" requirement relaxes to per-domain senders (`subscriptions` for cash/online, `artworks` for sales) sharing `core/mail_utils.py` (`send_best_effort`, parameterized per-audience renderer).
- `subscription-admin-controls`: `StripeEvent` admin registration moves to `core/admin.py` with the model; page behavior unchanged.
- `stripe-observability`: `StripeEvent` audit row is `core.models.StripeEvent`; startup presence check is performed by `core/stripe.py` while `subscriptions/apps.py:ready` retains its fail-fast gate; logging sources unchanged.
- `artist-admin`: membership action buttons and `ArtistSubscription` inline remain on `ArtistAdmin` in `artworks/` and keep importing subscription-domain services — explicitly out of scope for the sale extraction.

## Impact

- Code: `subscriptions/services/{stripe_client,notifications,webhooks}.py`, `subscriptions/models.py`, `subscriptions/admin.py` (StripeEventAdmin registration moves), `subscriptions/apps.py` boot gate, new flat modules `artworks/{stripe_orders,sale_notifications,order_webhooks}.py`, `artworks/{views,services,admin,management/commands}`, new `core/{stripe,stripe_utils,stripe_compat,mail_utils}.py`, `core/{models,admin}.py`, `core/migrations/0001_initial.py`, `project/urls.py` (import path of webhook view only), ~43 test mock strings, `emails-track.md`, `docs/{stripe-subscriptions,testing-stripe,stripe-account-setup,artwork-sales,enredarte-overview}.md`.
- DB: `core` gains its first migration (`0001_initial` creates `core_stripeevent`); a dependent `subscriptions` migration copies `subscriptions_stripeevent` rows then deletes the old model. Shared-Postgres worktrees must migrate from one sibling at a time.
- Systems: none externally — Stripe dashboard webhook URL, secrets, Checkout metadata, email subjects/bodies, and public REST paths unchanged.
