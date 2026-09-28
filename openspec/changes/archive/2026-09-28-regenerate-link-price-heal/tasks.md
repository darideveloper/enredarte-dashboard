## 1. Shared heal helper

- [x] 1.1 Add `_checkout_with_price_heal(sub, artist, plan)` in `artworks/admin.py` returning `(session, healed)`: empty-price auto-create (+ Spanish monto hint on `amount <= 0` failure), checkout via `_create_session_recovering_stale_customer`, `_is_stale_price_error` regen + exactly one retry, fail-loud logging.
- [x] 1.2 Refactor `generate_link` onto the helper with no behavior change (same loud regenerated message, same `update_fields` save).

## 2. Regenerate heal wiring

- [x] 2.1 Mirror the price-only `_billing_blocked` bypass in `regenerate_link` (still block on missing email / paused signups).
- [x] 2.2 Route `regenerate_link` expired-link checkout through the helper; healed success shows Spanish regenerated-price message.
- [x] 2.3 Verify `expire_or_reuse_session` fast-path and cash guards untouched; `open_portal`/`sync_from_stripe` unchanged.

## 3. Tests (Django only: `venv/bin/python manage.py test`)

- [x] 3.1 Regenerar heals stale `resource_missing` price: retries once with fresh `price_xxx`, shows regenerado message, persists `signup_url`.
- [x] 3.2 Regenerar auto-creates on empty `stripe_price_id` with valid amount.
- [x] 3.3 Heal-then-retry-failure: `Stripe no respondió`, `302`, no third attempt, no partial URL.
- [x] 3.4 Auth/non-stale error: zero `ensure_stripe_price` calls, `Stripe no respondió`, `302`.
- [x] 3.5 Zero-amount auto-create shows Spanish monto hint.
- [x] 3.6 Full `subscriptions` suite green.

## 4. Docs

- [x] 4.1 Update `docs/stripe-subscriptions.md` link-generation section: Regenerar heals identically to Generar.
