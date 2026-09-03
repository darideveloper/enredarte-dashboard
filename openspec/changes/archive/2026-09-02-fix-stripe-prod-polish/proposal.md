## Why

Three sequential prod 500s on `GET /admin/artworks/artist/<id>/sync-from-stripe/` (ListObject `subs[0]`, StripeObject `.get` blocked in v15, `Decimal` not JSON serializable) were fixed via `sget`/`to_plain_dict` DRY compat (`artworks/admin.py:505`, `subscriptions/services/stripe_compat.py`, `subscriptions/models.py:273`, `subscriptions/webhooks.py:167`). Post-fix deep audit (3 parallel explore agents, `/stripe/stripe-python` v15 migration guide) found ~34 gaps; the money path is now v15-ready, but 1 CRITICAL live-preview bug remains and 4 WARNING prod 500 paths plus missing logging/version pinning will cause the next outage. Fix the remaining high-value gaps in one polish change before the next deploy.

## What Changes

- **CRITICAL C1** — Fix `BillingPlanAdmin.change_view` (`subscriptions/admin.py:116-117`) still calling `recurring.get` on nested `StripeObject` via `isinstance(dict)` mis-classification; replace with `sget(recurring,"interval","") or ""`. ONE line, no `isinstance` branch.
- **W1** — Add `try/except stripe.error.StripeError → messages.error + redirect` to 4 `ArtistAdmin` actions that currently bubble to 500: `generate_link` (`artworks/admin.py:404,408`), `regenerate_link` (`455,458`), `open_portal` (`487`), `sync_from_stripe` (`501,504`). Add `logger.warning/exception` + 4 tests.
- **W2** — Keep webhook rollback semantics (`subscriptions/webhooks.py:182-193` one `transaction.atomic` wrapping `StripeEvent.create` + handler → rollback on crash, 500 for Stripe retry). Align `docs/stripe-subscriptions.md:132` + `openspec/specs/stripe-webhook-handler` spec to describe rollback (currently says error persisted outside atomic, contradicting `tests.py:348`).
- **W3** — Add observability: `project/settings.py` `LOGGING` (console JSON, level INFO, loggers `django`, `subscriptions`, `artworks` + optional `stripe` pass-through if configured), `logger.exception` on webhook crash, `logger.warning` on `BillingPlanAdmin.change_view` fallback `"(no se pudo confirmar)"`, `logger.info` on `plan_sync`/`ArtistAdmin` Stripe successes.
- **W4** — `subscriptions/services/plan_sync.py:40-62` Stripe calls outside `transaction.atomic`: keep outside (orphan acceptable) but add `try/except` around `archive_price` with `logger.warning("orphan price %s", new_price_id)` and doc comment. No DB change, retry creates new price as before.
- **S1** — Pin `requirements.txt:29` `stripe>=15.5.1,<16` + `subscriptions/apps.py:ready` `ImproperlyConfigured` when `ENV!="dev"` and `STRIPE_SECRET_KEY` empty or `STRIPE_WEBHOOK_SECRET` not `whsec_*`; warn if `STRIPE_API_VERSION` empty.
- **Batch (W5/S3/S4/N1/N3)** — Small guards: `subscriptions/webhooks.py:109` guard `if period_end is not None: set current_period_end` (avoid wiping on empty `lines.data`); `subscriptions/models.py:274` unwrap `customer` expanded `{"id":...}` dict → `cus_id`; add `checkout.session.expired` handler (clear `signup_url`, notify); fix `artworks/admin.py:512-514` double-save (remove second `save(update_fields=["customer_email"])`, set `customer_email` before `apply_stripe_payload`); make `subscriptions/admin.py:130` thread-safe via `request._stripe_live_summary` instead of `self._stripe_live_summary`; add 2 edge tests (empty invoice lines, unknown `map_stripe_status("weird")→PENDING`).
- **BREAKING: none** — all changes backward-compatible, no migration, no schema change.

## Capabilities

### New Capabilities

- `stripe-observability`: Centralized logging for Stripe webhooks, admin actions, and plan sync (LOGGING dict for `subscriptions`/`artworks`/`django` + optional `stripe` logger pass-through, logger calls, optional `SENTRY_DSN` env pass-through without new dep). No new user-facing API, only ops visibility.

### Modified Capabilities

- `artist-subscription-actions`: Error handling contract for the four Unfold `actions_detail` (`generate_link`, `regenerate_link`, `open_portal`, `sync_from_stripe` at `artworks/admin.py:388,432,477,490`) — Stripe failures must return `302` + `messages.error` not `500`; `sync_from_stripe` single-save and expanded-customer unwrap. Addresses double-save N1 and `customer.email` via `sget` N2.
- `subscription-admin-controls`: `BillingPlanAdmin` live preview (`subscriptions/admin.py:107-131`) — `recurring` interval must use `sget` (C1), `except Exception` narrowed to `StripeError` + `logger.warning`, thread-safe request storage (N3). Covers `POST /subscriptions/admin/artists/<id>/sync-from-stripe/` idempotency doc divergence.
- `stripe-webhook-handler`: Keep single-transaction rollback semantics (`subscriptions/webhooks.py:182`) and align spec/docs to it (W2); add `invoice` empty-lines guard (W5) and `checkout.session.expired` (S4); ensure `Decimal`/`ListObject` already handled via `to_plain_dict(for_json=True)` remains.
- `admin-editable-price`: `subscriptions/services/plan_sync.py:40-62` documents orphan price on `archive_price` failure and logs warning (W4); idempotence check remains but logs.

## Impact

- **Affected code:** `subscriptions/admin.py` (C1, thread-safe), `artworks/admin.py` (W1, N1/N2, `customer.email` `sget`), `subscriptions/services/plan_sync.py` (W4 orphan log), `subscriptions/services/stripe_compat.py` (already correct, reused), `subscriptions/webhooks.py` (W5, S4, logging), `subscriptions/models.py` (S3 unwrap), `project/settings.py` (LOGGING), `subscriptions/apps.py` (startup check), `requirements.txt` (pin), `docs/stripe-subscriptions.md` + `openspec/specs/stripe-webhook-handler/spec.md` (W2 alignment), `subscriptions/tests.py` (+~10 tests: 4 StripeError admin, 1 LivePreview StripeObject, 2 webhook edges, 1 map_status, 1 plan_sync orphan, 1 sync double-save).
- **Systems:** Django admin (`/admin/artworks/artist/<id>/change/*`, `/admin/subscriptions/billingplan/<id>/change/`), Stripe webhooks (`POST /webhooks/stripe/`), `BillingPlan` price sync, `JSONField` `raw_state`/`payload`. Public APIs, migrations, Stripe Dashboard unchanged.
- **Risks:** Low — 1-line `sget` fix already proven in `StripeCompatTest`; `StripeError` wraps match existing `BillingPlanAdmin.save_model` pattern; logging is additive; pin `<16` prevents silent 16.x break, startup check fails fast only when env missing (guarded by `ENV!="dev"`). Verified against `stripe>=15.5.1` docs (`/stripe/stripe-python` v15: `StripeObject` no longer `dict`, `Decimal` via `for_json=True`, `to_dict` replaces `dict()`/`dict.get`).
