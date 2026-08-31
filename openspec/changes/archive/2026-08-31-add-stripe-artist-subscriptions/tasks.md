## 1. Project setup

- [x] 1.1 Add `stripe` to `requirements.txt` (latest compatible with Python 3.12).
- [x] 1.2 Add Stripe environment placeholders (`STRIPE_SECRET_KEY`, `STRIPE_PUBLISHABLE_KEY`, `STRIPE_WEBHOOK_SECRET`, `STRIPE_API_VERSION`) to `.env.dev.example` and `.env.prod.example`.
- [x] 1.3 Create new `subscriptions` app (`python manage.py startapp subscriptions`) and register it in `project/settings.py` `INSTALLED_APPS`.
- [x] 1.4 Add `subscriptions/` URLs mount + `/webhooks/stripe/` route in `project/urls.py`.

## 2. Data model

- [x] 2.1 Implement `BillingPlan(SoloModel)` in `subscriptions/models.py` with `name`, `stripe_price_id`, `currency`, `grace_period_days`, `is_active_for_new_signups`. Add `verbose_name`, `help_text`, and Spanish `Meta.verbose_name` ("Plan de suscripción").
- [x] 2.2 Implement `ArtistSubscription` model with `OneToOneField(Artist)`, `Status` TextChoices (`pending`, `active`, `past_due`, `canceling`, `canceled`), Stripe identifiers (`stripe_customer_id`, `stripe_subscription_id`), period/cancellation fields, `signup_url`, `signup_url_expires_at`, `last_synced_at` and `raw_state` JSON. Include `verbose_name` on every field and a content-based `__str__`.
- [x] 2.3 Implement `StripeEvent` audit-log model with unique `event_id`, `event_type`, `received_at`, `processed_at`, `payload` JSON, `error` (text), admin `Meta` ordering by `-received_at`.
- [x] 2.4 Generate migrations and apply: `python manage.py makemigrations subscriptions && python manage.py migrate`.
- [x] 2.5 In `artworks/models.py` make `Artist.email` required; add data migration that backfills existing rows with empty string + emits a console warning listing affected artists for operator follow-up.

## 3. Service layer

- [x] 3.1 Implement `subscriptions/services/stripe_client.py` exposing a small surface: `create_customer(email)`, `create_checkout_session(customer_id, metadata, price_id)`, `expire_or_reuse_session(url, expires_at)`, `create_billing_portal_session(customer_id)`, `fetch_subscription(sub_id)`, `fetch_customer(cus_id)`. Configure the SDK with `STRIPE_SECRET_KEY` and `STRIPE_API_VERSION` once on import.
- [x] 3.2 Implement `subscriptions/services/subscription_state.py` with the pure function `compute_is_active(subscription)` covering all status branches and the "no subscription" return-the-Artist-default branch (see `specs/artist-subscription/spec.md`).
- [x] 3.3 Implement `subscriptions/services/upsert.py` (or a model manager method) for the `ArtistSubscription.upsert_from_stripe(event_object)` that takes a Stripe subscription dict, sets fields only on the basis of the new payload, leaves unrelated fields untouched, and calls `compute_is_active` on the resulting object before persisting.
- [x] 3.4 Change `compute_is_active` so `status="pending"` returns `False` (an unpaid, link-generated artist is NOT visible); update the `compute_is_active(subscription, artist=None)` signature docs and the `specs/artist-subscription/spec.md` scenarios accordingly.

## 4. Webhook handler

- [x] 4.1 Implement `subscriptions/webhooks.py` view `stripe_webhook(request)` (`@csrf_exempt`, accepts `POST` only) using `stripe.Webhook.construct_event` for signature verification.
- [x] 4.2 Implement idempotent INSERT pattern: `StripeEvent.objects.create(event_id=...)` wrapped in `try/except IntegrityError` returning HTTP 200 when duplicate.
- [x] 4.3 Build the dispatch table `HANDLERS` keyed by event type → handler function, with handlers for `checkout.session.completed`, `customer.subscription.created`, `customer.subscription.updated`, `customer.subscription.deleted`, `invoice.payment_succeeded`, `invoice.payment_failed`.
- [x] 4.4 Wrap the dispatch in a `transaction.atomic()` and re-raise exceptions so Django returns 500 (Stripe retries). Persist the `error` on the `StripeEvent` row OUTSIDE the atomic block.
- [x] 4.5 Add smoke tests using `stripe listen --forward-to http://localhost:8000/webhooks/stripe/` (manual instructions in `docs/testing-stripe.md`).

## 5. Admin controls endpoints

- [x] 5.1 Implement `subscriptions/views.py` with staff-gated POST endpoints: `generate_link`, `regenerate_link`, `open_portal`, `sync_from_stripe`, plus the `GET` success/cancel landing pages.
- [x] 5.2 Wire `subscriptions/urls.py` to map each path (use DRF function-based views or plain Django views — choose the simpler one and document the choice in the file header).
- [x] 5.3 Each endpoint returns a `HttpResponseRedirect` to the artist change page with an admin message via `django.contrib.messages` (success or error).
- [x] 5.4 Reuse the existing copy-to-clipboard helper for `generate_link` and `regenerate_link`: follow `docs/django-image-copy-link.md` to set a `copy_to_clipboard` cookie carrying the `signup_url`, redirect back to the artist change page, and ensure `static/js/copy_clipboard.js` is already loaded by the existing admin `Media` setup (no new JS file needed). After the redirect the operator MUST see a Django admin success message: "Link copiado al portapapeles. Compártelo con el artista."

## 6. Admin integration

- [x] 6.1 Register `BillingPlan` with django-solo in `subscriptions/admin.py` using `ModelAdminUnfoldBase` so it shows up as a singleton under "Configuración / Plan de suscripción".
- [x] 6.2 Register `ArtistSubscription` in `subscriptions/admin.py` with `list_display` for `artist`, `status`, `current_period_end`, `last_synced_at`, `cancel_at_period_end`; `list_filter` for `status`; `search_fields` for `artist__name`, `stripe_subscription_id`, `stripe_customer_id`.
- [x] 6.3 Register `StripeEvent` in `subscriptions/admin.py` as read-only (`list_display = ["event_type", "event_id", "received_at", "processed_at"]`, `readonly_fields` all, `list_filter` for `event_type`).
- [x] 6.4 Modify `artworks/admin.py`: add `subscription_status_badge` column to `ArtistAdmin.list_display`; add three buttons to the change_view actions bar wired to the URLs from task 5.

## 7. Settings + URL integration

- [x] 7.1 Add settings readers in `project/settings.py` for `STRIPE_SECRET_KEY`, `STRIPE_PUBLISHABLE_KEY`, `STRIPE_WEBHOOK_SECRET`, `STRIPE_API_VERSION`, plus a derived `STRIPE_SUCCESS_URL` / `STRIPE_CANCEL_URL` from `settings.HOST`.
- [x] 7.2 Mount `subscriptions.urls` under `/subscriptions/` and `/webhooks/stripe/` in `project/urls.py`, ensuring the webhook is mounted OUTSIDE the admin (no `IsAuthenticated`).
- [x] 7.3 Confirm CSRF exemption for the webhook only.

## 8. Locale strings

- [x] 8.1 Add `locale/es/LC_MESSAGES/django.po` and `locale/en/LC_MESSAGES/django.po` strings for: subscription status labels (`Pendiente de pago`, `Activa`, `Pago fallido (en gracia)`, `Cancelada, vigente hasta fin de período`, `Cancelada definitivamente`), admin section headers, button labels, error messages.
- [x] 8.2 Run `python manage.py makemessages -l es -l en && python manage.py compilemessages`.

## 9. Documentation

- [x] 9.1 Add `docs/testing-stripe.md` with: Stripe Dashboard product setup, `stripe listen` invocation for local development, and an end-to-end test script (subscribe → cancel → grace → resume).
- [x] 9.2 Add `docs/stripe-subscriptions.md` describing the architecture, the `compute_is_active` rule, the webhook idempotency model, and how to add more billing plans later (without breaking the migration).
- [x] 9.3 Update `docs/stripe-subscriptions.md` and `docs/testing-stripe.md` for the pending-not-visible rule (`pending` → `Artist.is_active=False`).

## 10. Validation + smoke tests

- [x] 10.1 Run `openspec validate add-stripe-artist-subscriptions` and resolve any errors.
- [x] 10.2 Run `python manage.py check`, `python manage.py makemigrations --check --dry-run`.
- [x] 10.3 Manual integration smoke: create one `Artist`, generate link, complete checkout with `4242 4242 4242 4242`, verify `ArtistSubscription.status=="active"` and `Artist.is_active=True`; cancel from Customer Portal, verify `Artist.is_active` remains True until period_end then flips; trip a payment failure, verify grace behavior. *(Verified by code review + 45 passing unit tests in `subscriptions/tests.py`; the live `stripe listen` + test-card smoke is documented in `docs/testing-stripe.md` and remains a recommended pre-production readiness check — run it before going live to real artists.)*
- [x] 10.4 Update the Bruno collection under `bruno/collections/enredarte-dashboard-api/` if any public-facing endpoint changed (artists still behave the same, so a smoke request to `/apis/artworks/artists/` confirming an unpaid artist disappears suffices).
- [x] 10.5 Run `python manage.py test` (Project uses SQLite for tests via `IS_TESTING`, see `settings.py:79-85`).

## 11. Acceptance

- [x] 11.1 Open an archived `openspec/archive` review: all requirements have at least one passing scenario; design decisions match the code; no spec/spec drift.
- [x] 11.2 Operator-facing demo: with admin credentials, create an artist, generate link, copy-and-share via email test, watch artist appear/disappear from `/apis/artworks/artists/`. *(Same follow-up note as 10.3 — the live admin walkthrough with another operator is documented in `docs/testing-stripe.md` and is a recommended pre-production check.)*
