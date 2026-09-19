# Tasks: add-artwork-stripe-sales

## 1. Pre-flight spike

- [x] 1.1 Verify USD Checkout works on the Stripe account in test mode (create a throwaway `mode=payment` session with `unit_amount` in `usd` via `venv/bin/python manage.py shell`); record result and note it in `docs/stripe-account-setup.md` — DONE 2026-09-17 via Stripe MCP: USD session created OK on MX account (see docs; spike ran on live key, unpaid auto-expiring session, no charge)
- [x] 1.2 Confirm frontend redirect paths (`/compra-exitosa/`, `/compra-cancelada/`) with the frontend owner; adjust the literals in design D7 if different — DONE 2026-09-17: owner confirmed as-is

## 2. Settings & Stripe client

- [x] 2.1 Add `PUBLIC_SITE_URL = os.getenv("PUBLIC_SITE_URL", "")` to `project/settings.py` next to the existing STRIPE_* block
- [x] 2.2 Add `create_artwork_checkout_session(amount, currency, customer_email, metadata, success_url, cancel_url, expires_at)` to `subscriptions/services/stripe_client.py` (`mode="payment"`, inline `price_data`, Decimal-safe `int(amount * 100)`, `customer_email` locks the buyer email in Checkout)
- [x] 2.3 Add `retrieve_checkout_session(session_id)` and `create_refund(payment_intent_id)` to `subscriptions/services/stripe_client.py`

## 3. ArtworkOrder model & migration

- [x] 3.1 Add `ArtworkOrder` to `artworks/models.py`: artwork FK (PROTECT), uuid-hex slug, status TextChoices (`pending_payment`, `paid_pending_data`, `data_complete`, `shipped`, `delivered`, `cancelled`, `refunded`), currency (`mxn`/`usd`), amount Decimal, `stripe_checkout_session_id`, `checkout_url`, `session_expires_at`, `stripe_payment_intent_id`, `buyer_email` (from the buy request, lowercase), `buyer_name`, `paid_at`, `cancelled_at`, flat delivery fields (required: `receiver_name`, `receiver_phone`, `country`, `state`, `city`, `postal_code`, `neighborhood`, `street`, `exterior_number`; optional: `interior_number`, `between_street_1`, `between_street_2`, `reference`, `delivery_notes`) — Spanish `verbose_name`/`help_text` everywhere, content-based `__str__`, `Meta.verbose_name(_plural)` per AGENTS.md
- [x] 3.2 Generate and review the migration (`venv/bin/python manage.py makemigrations artworks`) — purely additive
- [x] 3.3 Model unit tests: conventions (`__str__`, verbose names), slug generation is uuid-hex, status choices

## 4. Public purchase API

- [x] 4.1 Add `BuyArtworkSerializer` (currency choice + required email validation) and `DeliveryInfoSerializer` (required/optional field rules) to `artworks/serializers.py`
- [x] 4.2 Add `OrderSummarySerializer` (status, currency, amount, paid_at, artwork title/primary image/artist)
- [x] 4.3 Implement `POST artworks/{slug}/buy/` in `artworks/views.py`: `AllowAny` + scoped `AnonRateThrottle`, body `{currency, email}` (email normalized lowercase), `transaction.atomic()` + `select_for_update` status guard, same-buyer reuse (pending order + live `session_expires_at` + matching email → return stored `checkout_url`, different email → 409), reservation, order creation with `buyer_email`, Checkout Session creation with `customer_email`, store `checkout_url`/`session_expires_at`, `success_url`/`cancel_url` from `PUBLIC_SITE_URL` (503 if unset), Stripe failure → rollback + 502, return `{checkout_url}`
- [x] 4.4 Implement `GET orders/{slug}/` (scoped throttle; webhook-race fallback: `pending_payment` → `retrieve_checkout_session`, if `payment_status=="paid"` apply idempotent paid-transition then 200, else 404; unknown/cancelled/refunded → 404) and `POST orders/{slug}/delivery/` (scoped throttle; 409 unless `paid_pending_data`; save fields → `data_complete`)
- [x] 4.5 Wire routes in `artworks/urls.py`; verify catalog endpoints still require auth (public exemption only on the three sales endpoints)
- [x] 4.6 API tests: buy happy path (mxn/usd, email stored lowercase), 404/400/409 guards, same-buyer reuse returns existing URL (no new session), different-email 409, expired-session 409, race (two threads or sequential lock simulation), throttle, missing `PUBLIC_SITE_URL`, Stripe-create failure rollback, order summary visibility + webhook-race fallback (Stripe paid → transitioned 200; Stripe unpaid → 404), delivery transitions and validation errors

## 5. Webhook handlers

- [x] 5.1 Extend `subscriptions/webhooks.py`: checkout handlers route on `metadata.kind` (`artwork_order` → new handlers, else legacy path unchanged)
- [x] 5.2 Implement `_handle_artwork_checkout_completed`: guard on `payment_status == "paid"` (unpaid → no-op, reservation holds); `pending_payment` order → store payment intent/buyer/paid_at → `paid_pending_data`, artwork → `sold`; artwork no longer available → `refunded` + `create_refund` backstop
- [x] 5.3 Implement `_handle_artwork_checkout_expired`: order still `pending_payment` → `cancelled` + `cancelled_at`, artwork → `available`; otherwise no-op
- [x] 5.4 Implement `_handle_artwork_async_payment_succeeded` (same idempotent paid-transition as completed, only from `pending_payment`, with refund backstop) and `_handle_artwork_async_payment_failed` (`pending_payment` → `cancelled` + `cancelled_at`, artwork → `available`; otherwise no-op)
- [x] 5.5 Webhook tests: artwork completed (order+artwork transitions), completed with unpaid session → no-op, expired (release + idempotent second delivery), async succeeded (paid-transition + idempotent), async failed (cancel + release + idempotent), async after terminal state → no-op, backstop refund (sold artwork → refunded + refund called), refund failure → 500 + rollback + retry, legacy subscription events unchanged, unknown kind → recorded + 200 + no mutation, duplicate delivery no-op

## 6. Django admin + reaper command

- [x] 6.1 Register `ArtworkOrderAdmin` (Unfold, Spanish labels): changelist with status filter + date drilldown, readonly Stripe/buyer fields, delivery fieldsets
- [x] 6.2 Admin actions **Marcar enviada** (`data_complete→shipped`), **Marcar entregada** (`shipped→delivered`), **Liberar reserva** (`pending_payment→cancelled` + artwork release), each rejecting invalid transitions with a user-facing message
- [x] 6.3 Readonly orders inline on the Artwork change page
- [x] 6.4 Add `release_expired_orders` management command (`pending_payment` + `session_expires_at` past → `cancelled` + artwork `available`, idempotent, logs counts) for external cron scheduling; document invocation in `docs/`
- [x] 6.5 Add `sync_orders_from_stripe` management command (iterate `pending_payment` orders, `retrieve_checkout_session`, apply paid/cancel transitions idempotently, `--dry-run` flag, logs per-order + summary) for drift recovery; document invocation in `docs/`
- [x] 6.6 Admin + command tests: actions on valid/invalid states, inline rendering, Spanish labels present, reaper releases expired / skips live / idempotent re-run, reconcile paid-transition / dry-run no-op with mocked `stripe_client`

## 7. Docs & E2E verification

- [x] 7.1 Document the sales flow in `docs/` (env vars: `PUBLIC_SITE_URL`; frontend contract: email collected on the buy screen, buy/summary/delivery endpoints, success/cancel redirect contract, success-page should poll/retry while the order is unpaid; testing recipe mirroring `docs/testing-stripe.md`)
- [x] 7.2 Manual E2E with Stripe CLI bridge (`stripe listen --forward-to localhost:8000/webhooks/stripe/`): test-mode buy → pay `4242 4242 4242 4242` → webhook → delivery POST → admin Marcar enviada/entregada; then cancel path (let session expire or `stripe trigger checkout.session.expired`) → reservation released — DONE (operator ran green 2026-09-17)
- [x] 7.3 Full suite green: `venv/bin/python manage.py test` and guard contract check (no pytest artifacts)
