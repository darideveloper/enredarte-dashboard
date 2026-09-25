## 1. Baseline and safety net

- [x] 1.1 Run `venv/bin/python manage.py test` on a clean tree and record the green baseline (phase gate reference).
- [x] 1.2 Grep and record all sale cross-imports: `subscriptions.services.stripe_client.(create_artwork_checkout_session|retrieve_checkout_session|create_refund)`, `subscriptions.services.notifications.send_sale_*`, `subscriptions/email/sale_`, `subscriptions.models import.*StripeEvent`, `from subscriptions` inside `artworks/` sale modules.

## 2. Phase 1 — shared mail helpers + sale senders + templates (no DB)

- [x] 2.1 Create `core/mail_utils.py` with `send_best_effort` and the per-audience renderer **parameterized to accept a full template base path** (remove the hardcoded `subscriptions/email/` prefix from `notifications.py:164-165`); update cash/online callers in `subscriptions/services/notifications.py` to pass `subscriptions/email/*` bases and import from `core.mail_utils`. Add a `"core"` logger (`console`, `INFO`, `propagate: False`) to `project/settings.py:LOGGING`.
- [x] 2.2 Create `artworks/sale_notifications.py` with `_SALE_AUDIENCES`, `_SALE_SUBJECTS`, `_sale_context`, `_send_sale`, `artwork_artist_email`, all `send_sale_*` (behavior identical, shared renderer from `core.mail_utils`, template bases `artworks/email/sale_*`).
- [x] 2.3 Move 36 `sale_*` templates to `artworks/templates/artworks/email/` (same basenames/bodies), delete `subscriptions/templates/subscriptions/email/sale_*`.
- [x] 2.4 Cut sale block from `subscriptions/services/notifications.py`; rewrite all sale callers to `artworks.sale_notifications`, replacing `notifications.send_best_effort(...)` with `core.mail_utils.send_best_effort(...)`: `artworks/views.py:253,352,392`, `artworks/services.py:87,115,122`, `artworks/admin.py:1429,1442,1461`, `sync_orders_from_stripe.py:49,55`, `release_expired_orders.py:28`, and the sale branches in `subscriptions/webhooks.py:82,89,117,144`. Keep subscription-domain `notifications`/`stripe_client` imports in `artworks/admin.py` for membership actions (out of scope). Update `subscriptions/webhooks.py:265,285` (online) to `core.mail_utils.send_best_effort` + subscriptions `notifications`.
- [x] 2.5 Update sale mail tests in `artworks/tests.py` (module import + template paths); add/extend a render test asserting a sale message resolves `artworks/email/sale_*` and an online message resolves `subscriptions/email/online_*`; gate: `venv/bin/python manage.py test artworks subscriptions`.

## 3. Phase 2 — Stripe SDK init + sale Stripe client to artworks (no DB)

- [x] 3.1 Create `core/stripe.py` (import-time `stripe.api_key`/`stripe.api_version` + `STRIPE_*` presence check); make `subscriptions/services/stripe_client.py` and `artworks/stripe_orders.py` import it.
- [x] 3.2 Create `artworks/stripe_orders.py` with `create_artwork_checkout_session`, `retrieve_checkout_session`, `create_refund` (identical Stripe calls); cut them from `subscriptions/services/stripe_client.py`.
- [x] 3.3 Rewrite all callers (`buy`, `OrderSummaryView`, reconcile, `sync_orders_from_stripe`, webhook/order paths) and all mock strings in `artworks/tests.py` (39) and `subscriptions/tests.py` sale refund patches (2409/2423/2636/2653) to `artworks.stripe_orders.*`; gate: full `manage.py test`.

## 4. Phase 3 — sale webhook logic delegated (no DB, single URL preserved)

- [x] 4.1 Create `artworks/order_webhooks.py` with artwork-branch logic (paid-transition + double-sale refund backstop, expired release, async succeeded/failed) as pure order+session functions, using `artworks.stripe_orders`, `artworks.sale_notifications`, and `core.mail_utils.send_best_effort`.
- [x] 4.2 Slim `subscriptions/webhooks.py` to envelope (verify + `StripeEvent` insert via `core.models` + atomic block + `HANDLERS`) delegating `metadata.kind == "artwork_order"` sessions to `artworks.order_webhooks`; `project/urls.py` path unchanged.
- [x] 4.3 Gate: webhook tests incl. duplicate delivery, crash-rollback, double-sale refund, cash-row guards, async OXXO `checkout.session.async_payment_*`.

## 5. Phase 4 — shared primitives to core (DB migration)

- [x] 5.1 Add `core.models.StripeEvent` (identical fields/meta), `core/stripe_utils.py` (`epoch_to_datetime`), move `stripe_compat.py` to `core/stripe_compat.py`; update every import in both apps (`subscriptions/{models,webhooks,admin,services/plan_sync}`, `artworks/{admin,services,views}`) and in `subscriptions/tests.py:22`.
- [x] 5.2 Generate `core/migrations/0001_initial.py` (`StripeEvent`); write the `subscriptions` migration with `dependencies = [("core", "0001_initial"), ...]` that `RunPython`-copies `subscriptions_stripeevent` → `core_stripeevent` via `bulk_create` (preserving `event_id`/`event_type`/`received_at`/`processed_at`/`payload`/`error`), asserts count equality, then `DeleteModel`s the old model; reverse migration is a guarded no-op. Plain copy — no `SeparateDatabaseAndState`/table rename. Move `StripeEventAdmin` to `core/admin.py`.
- [x] 5.3 Migrate from ONE sibling only (shared Postgres gotcha), verify row counts, run full suite; update `docs/stripe-subscriptions.md` (architecture diagram: `StripeEvent (core/models.py)`, "only file that imports stripe" line), `docs/testing-stripe.md`, `docs/stripe-account-setup.md`, `docs/artwork-sales.md`, `docs/enredarte-overview.md`, `emails-track.md`. Confirm the new `subscription-admin-controls`/`stripe-observability`/`artist-admin` deltas apply cleanly at archive.
- [x] 5.4 Final grep gates: zero `from subscriptions` in `artworks` sale modules (`stripe_orders`, `sale_notifications`, `order_webhooks`, sale paths in `views`/`services`/commands); zero `subscriptions/email/sale_` in code and templates; zero `subscriptions.services.stripe_client.(create_artwork|retrieve_checkout|create_refund)`; zero `subscriptions.models import.*StripeEvent`; zero `notifications.send_best_effort` call sites (all now `core.mail_utils`); zero hardcoded `subscriptions/email/` in the shared renderer; full `manage.py test` green.

## 6. Feature regression verification (prove nothing broke)

- [x] 6.1 Sales lifecycle: buy reserves + `201` checkout_url; same-buyer reuse `200` sends no mail; unavailable `409`; order-summary paid fallback transitions; delivery POST reaches `data_complete`; admin shipped/delivered transitions mail buyer+admin.
- [x] 6.2 Stripe edge cases: double-sale refund backstop, lazy `reconcile_stale_reservations` (release + paid), `sync_orders_from_stripe`, `release_expired_orders`, async OXXO succeeded/failed, webhook duplicate-delivery `200` + crash-rollback `500`.
- [x] 6.3 Memberships untouched: cash pending/active/canceled + cron reminders/overdue/deactivated mails; online `canceling`/`canceled` mails transition-gated; `BillingPlan` price sync; artist admin generate/regenerate link, portal, sync-from-stripe, cash actions; `compute_is_active` visibility rules.
- [x] 6.4 Cross-cutting: all 36 sale + 8 online + 28 cash templates render TXT+HTML; `EMAILS_NOTIFICATIONS` empty skips admin only; admin `StripeEvent` audit page loads newest-first with payload; single `POST /webhooks/stripe/` still the only endpoint (Stripe CLI replay).
