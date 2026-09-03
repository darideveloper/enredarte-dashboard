## Context

`enredarte-dashboard` integrates Stripe via `stripe>=15.5.1` (`requirements.txt:29`, `STRIPE_API_VERSION=2026-07-29.dahlia`). The v15 migration (per `/stripe/stripe-python` wiki: `StripeObject` no longer `dict`, `Decimal` for `unit_amount_decimal`/`fx_rate`, `to_dict(for_json=True)`) broke three prod paths on `GET /admin/artworks/artist/5/sync-from-stripe/` in sequence: `ListObject subs[0]` at `stripe/_list_object.py:99`, `StripeObject.get` blocked at `stripe/_stripe_object.py:163`, `Decimal` not JSON serializable at `json/encoder.py:180`. Fixes landed: `artworks/admin.py:505` ListObject `.data` guard, `subscriptions/services/stripe_compat.py:10` `sget`/`to_plain_dict` DRY compat, `subscriptions/models.py:273` + `webhooks.py:167` `for_json=True` + `Decimal→str`. Deep audit (3 agents, exhaustive grep of `isinstance(dict)`, `.get`, `dict()`, `JSONField`) found ~34 gaps; money path is v15-ready, but 1 CRITICAL and 4 WARNING remain that will 500 again. This design consolidates the polish into one minimal change, per user choices gap-by-gap (Gap1 fix, Gap2 all-4, Gap3 keep-rollback, Gap4 logging, Gap5 savepoint+log, Gap6 pin+check, Gap7 batch).

Stakeholders: admin operators (`ArtistAdmin` Unfold actions), Stripe webhook operators (`StripeEventAdmin`), `BillingPlan` owners. Constraints: no new external dep, no migration, keep `stripe_client.py` single import boundary, stay `hasattr(subs,"data")` dual-shape compat for plain-list mocks, single-save for `sync_from_stripe`, thread-safe admin instance.

## Goals / Non-Goals

**Goals:**
- Make `BillingPlanAdmin.change_view` (`subscriptions/admin.py:107-131`) show `Confirmado por Stripe` for real `StripeObject` `recurring` (C1) via uniform `sget`.
- Make 4 `ArtistAdmin` actions (`artworks/admin.py:388,432,477,490`) return `302 + messages.error("Stripe no respondió")` on `StripeError` instead of `500` (W1).
- Add observability: `LOGGING` console JSON + `logger.*` calls in webhooks/admin/plan_sync so ops can trace money-path calls (W3).
- Document orphan price on `archive_price` failure with warning log (W4).
- Prevent silent 16.x break + misconfigured webhook: pin `stripe<16` and startup check (S1).
- Fix small guards: invoice empty lines guard, expanded `customer` unwrap, `checkout.session.expired`, double-save removal, thread-safe `request` storage (batch N1/N3/W5/S3/S4).

**Non-Goals:**
- Changing webhook rollback semantics (W2): keep single `transaction.atomic` (`webhooks.py:182`) and update spec/docs to match — no two-phase `error` persistence.
- Adding `dj-stripe`, idempotency keys, or Sentry SDK — `SENTRY_DSN` pass-through only if env present.
- Changing `BillingPlan` pricing logic, `STRIPE_PRICE_ID` sunset, or Stripe Dashboard wiring.
- Pagination beyond `limit=1` for `ListObject` or full `customer` expansion handling.

## Decisions

**D1 — Fix `recurring.get` via uniform `sget` (C1).**
*Rationale:* Smallest diff, DRY. `subscriptions/admin.py:116-117` currently `if isinstance(recurring,dict): recurring.get("interval")` — `StripeObject` in 11.x is `dict` subclass → `isinstance` True → blocked `.get` in 15.x. Alternative `if isinstance and not hasattr(to_dict)` is fragile; `sget(recurring,"interval","") or ""` handles plain dict, `StripeObject`, and `None` via ponytail ladder (`_stripe_object.py:198` `__getitem__` then `getattr`).
*Alternative:* Add `try: recurring.get` fallback — duplicates `sget` logic.

**D2 — `StripeError` handling at call site, not in `stripe_client` (W1).**
*Rationale:* `subscriptions/services/stripe_client.py:1-17` is thin wrapper with no policy; catching inside would hide caller’s redirect target and `messages` choice. Match existing `subscriptions/admin.py:139` `BillingPlanAdmin.save_model` pattern: `except stripe.error.StripeError as e: messages.error(request, f"Stripe no respondió: {e}"); logger.warning; return redirect(redirect_url)`. Caller stays responsible for UX (302 to `admin:artworks_artist_change`).
*Alternative:* Make `stripe_client` return `Result` union — over-engineered for 4 call sites.

**D3 — Keep webhook single-atomic rollback (W2, user choice A).**
*Rationale:* `subscriptions/webhooks.py:182` `with transaction.atomic(): StripeEvent.create + handler + processed_at` + `except IntegrityError: return 200` is intentionally retry-clean: on handler crash, whole row rolls back, Stripe retry is fresh (`tests.py:348` asserts `assertFalse(StripeEvent.objects.filter(evt_crash).exists())`). Two-phase with `error` persisted leaves partial row and requires test rewrite. User chose keep-rollback; we align `docs/stripe-subscriptions.md:132` + `openspec/specs/stripe-webhook-handler` spec to describe rollback, not error persistence.
*Alternative:* Two-phase savepoint with `record.error=str(e)` → spec-compliant but breaks current idempotency tests.

**D4 — LOGGING as `LOGGING` dict + `logger` per module, no new dep (W3).**
*Rationale:* `project/settings.py` currently has no `LOGGING` (`grep LOGGING` 0). Add `LOGGING = {"version":1, "disable_existing_loggers":False, "handlers":{"console":{"class":"logging.StreamHandler"}}, "loggers":{"django":{"handlers":["console"],"level":"INFO"},"subscriptions":{"handlers":["console"],"level":"INFO","propagate":False},"artworks":{"handlers":["console"],"level":"INFO","propagate":False}}}` style — console JSON-like, level `INFO` for prod, `WARNING` for change_view fallback. Optional `stripe` logger pass-through if configured. No `sentry_sdk` unless `SENTRY_DSN` env present (pass-through only). Keeps YAGNI.
*Alternative:* Add `django-structlog` + Sentry — grows deps for marginal gain.

**D5 — Plan sync orphan warning, keep outside atomic (W4, user choice B).**
*Rationale:* `subscriptions/services/plan_sync.py:40-62` does Stripe `create_price`/`set_product_default_price` before `65:82` `atomic` for `History`+`plan.save`. Moving Stripe inside atomic doesn’t help (Stripe calls are not transactional). Keep outside but wrap `archive_price` in `try/except stripe.error.StripeError: logger.warning("orphan price %s ...", new_price_id); raise` + doc comment “retry creates another price, orphan expected”. Tests already cover rollback of DB on Stripe errors (`tests.py:1120`).
*Alternative:* Wrap all in outer `transaction.atomic` with `savepoint` + `pg_advisory_xact_lock` — adds DB lock for rare race.

**D6 — Pin `stripe>=15.5.1,<16` + startup check (S1, user choice Pin+check).**
*Rationale:* Unbounded `>=15.5.1` lets `16.x` remove `stripe_id`/`to_dict_recursive` silently. Pin `<16` forces bump review. `subscriptions/apps.py:ready` check `if ENV!="dev" and (not STRIPE_SECRET_KEY or not STRIPE_WEBHOOK_SECRET.startswith("whsec_")): raise ImproperlyConfigured` fails fast on misconfigured prod where `construct_event(...,"")` would always 400. Mirrors `.env.dev:18` `whsec_xxxx` placeholder awareness.
*Alternative:* `==15.5.1` exact pin — too rigid for patch updates.

**D7 — Batch small guards in same change (user choice Fix batch now).**
*Rationale:* All touch same 3 files (`webhooks.py`, `models.py`, `artworks/admin.py`) already edited for W1/W5; bundling avoids churn.
- `webhooks.py:39` guard `if period_end is not None: sub.current_period_end = period_end` prevents wiping on empty invoice lines.
- `models.py:274` unwrap `customer` expanded `{"id":...}` → `cus_id = sget(customer,"id") if isinstance(customer,dict) else customer` (via `sget` + `isinstance` but `sget` handles StripeObject, so `if isinstance(cus, dict) and sget(cus,"id")` branch).
- `checkout.session.expired` handler: add `HANDLERS["checkout.session.expired"] = _handle_checkout_expired` clearing `signup_url`/expiry + `_sync_artist` (mirror `created` cleanup).
- `artworks/admin.py:512-514` remove double-save: set `sub.customer_email` before `apply_stripe_payload` (apply saves 8 fields + `raw_state`), remove `sub.save(update_fields=["customer_email"])` second save.
- `subscriptions/admin.py:130` thread-safe: `request._stripe_live_summary = ...` instead of `self._stripe_live_summary`.

## Risks / Trade-offs

- **Narrowed `except Exception` in `BillingPlanAdmin.change_view:126` → `except stripe.error.StripeError, Exception` with `logger.warning`:** Mitigation — keep broad fallback but log, so real bugs still surface as `"(no se pudo confirmar)"` but with trace.
- **Keeping webhook rollback loses `error` audit:** Mitigation — `logger.exception` on webhook crash provides trace; spec/docs updated to match; `StripeEvent.error` stays for manual ops.
- **Startup check may block prod with placeholder `whsec_xxxx`:** Mitigation — guard `ENV!="dev"` and `startswith("whsec_")`, dev stays `whsec_xxxx` placeholder, prod must set real secret (fail fast is desired).
- **Pin `<16` blocks security patch if 16.x is security fix:** Mitigation — Dependabot bump review, pin still allows `15.x` patches.
- **`sget` on `None` recurring:** Mitigation — `sget(None,"interval","")` returns `""` via early `if obj is None` guard (`stripe_compat.py:17`).
- **`LOGGING` dict merges with existing config:** Mitigation — set `disable_existing_loggers=False` so gunicorn/uvicorn handlers survive; keep console handler only, no file rotation.
- **`request._stripe_live_summary` thread-safety assumption:** Mitigation — if `display_stripe_live` called without `request` (e.g., list view), fallback to `"(no se pudo confirmar)"` with `logger.warning`.
- **Orphan price accumulation on `archive_price` failure:** Mitigation — `logger.warning` records `new_price_id`/`old_price_id`; retry creates another price, orphan remains in Stripe until manual archive (cost minimal, no DB drift).

## Migration Plan

- No migrations. Deploy code, no Stripe Dashboard change.
- `requirements.txt` pin requires `pip install -r requirements.txt` in prod image.
- Rollback: revert 7-file diff; `StripeObject` paths degrade to previous `"(no se pudo confirmar)"` but no DB state change.
- Verification: `python manage.py test subscriptions -v 2` (expect `73→~83` tests, new: 4 StripeError admin, 1 LivePreview StripeObject, 2 webhook edges, 1 map_status, 1 plan_sync orphan), `GET /admin/subscriptions/billingplan/1/change/` with real `Price` → `Confirmado por Stripe`, `GET /admin/artworks/artist/5/sync-from-stripe/` → `302`, Stripe error injection via `patch(..., side_effect=stripe.error.StripeError)` → `messages.error`.

## Open Questions

- None blocking. Optional follow-up: pass `idempotency_key` to `stripe.Price.create`/`Customer.create` (C5) — deferred; orphan warning suffices for now.
- `checkout.session.expired` status: decided — leave `status` as-is (typically `PENDING`), do not force `PENDING` explicitly; only clear `signup_url`/`signup_url_expires_at` and log. See `stripe-webhook-handler` spec (status remains pending).
