## 1. Mailer core (Approach A)

- [x] 1.1 Add generic triple-send helper + shared context (`order/artwork/artist/buyer/host/admin_url/checkout_url`) to `subscriptions/services/notifications.py`; keep cash senders untouched.
- [x] 1.2 Add 7 `send_sale_*` + `send_online_canceling` + `send_online_canceled` senders with exact Spanish subjects from specs; per-audience skip-and-log on blank address / empty admin list.
- [x] 1.3 Unit-test senders via `locmem` outbox: audience counts (`send_sale_paid` = buyer+artist+admin; `send_online_canceling`/`send_online_canceled` = artist+admin), subjects, skip-and-log branches (blank artist email, empty `EMAILS_NOTIFICATIONS`).

## 2. Templates (44 files)

- [x] 2.1 Create `sale_reserved_{buyer,admin}` + `sale_paid_{buyer,artist,admin}` TXT+HTML pairs (buyer-reserved carries `checkout_url` + expiry; paid carries receipt/delivery-link, sold notice, admin Stripe ids).
- [x] 2.2 Create `sale_delivery_complete_{buyer,artist,admin}` + `sale_shipped/delivered_{buyer,admin}` pairs (artist delivery body states address-sharing purpose, no payment ids).
- [x] 2.3 Create `sale_cancelled_{buyer,artist,admin}` + `sale_refunded_{buyer,artist,admin}` + `online_{canceling,canceled}[_admin]` pairs (refund bodies carry refund confirmation; admin bodies carry both slugs + payment-intent/refund ids; online-canceling says "visible until period end", online-canceled says "no longer visible").
- [x] 2.4 Render-test every pair (buyer/artist/admin × TXT/HTML): required elements present, Spanish-only, admin links resolve.

## 3. Sale firing points

- [x] 3.1 `buy` (`artworks/views.py`): post-commit best-effort reserved sends; reuse-`200` sends nothing; failure keeps `201`.
- [x] 3.2 Paid paths: webhook `_apply_artwork_paid`, reconcile `_apply_reconciled_paid`, `OrderSummaryView` fallback, `sync_orders_from_stripe` — send only when transition returns `True`; webhook paths via `transaction.on_commit`.
- [x] 3.3 Delivery + shipment: `OrderDeliveryView` post-transition sends; `marcar_enviada` / `marcar_entregada` admin actions send on success, warn on mail failure, send nothing on invalid transition — re-read the actually-changed rows after the bulk `.filter().update()` and send one mail per row that truly transitioned.
- [x] 3.4 Cancel paths: `expired`/`async_failed` webhooks, `release_expired_orders`, manual `Liberar reserva`, reconcile cancel — send only when `cancel_order` returns `True` (webhook/reconcile/reaper) or, for `liberar_reserva`'s direct per-row loop, only for rows actually transitioned (guarded by the `PENDING_PAYMENT` check); webhook paths via `on_commit`.
- [x] 3.5 Refund path: send after `create_refund` succeeds (both webhook + reconcile branches); refund raise → no mail, 500 for Stripe retry.

## 4. Online-cancelled firing point

- [x] 4.1 `customer.subscription.updated` (→ `canceling`) and `customer.subscription.deleted` (→ `canceled`) handlers: cash-guard first, then `on_commit` best-effort `send_online_canceling` / `send_online_canceled` respectively. The `canceling` mail SHALL be transition-gated — send only when the previous stored status was not already `canceling` (confirm by reading `raw_state`/prior `status` before `apply_stripe_payload` overwrites it, or compare before/after). Duplicate `event_id` sends nothing; mail failure keeps 200.

## 5. Verification

- [x] 5.1 `venv/bin/python manage.py test subscriptions artworks --verbosity=2` green (394 tests); new tests cover: reserved buy mails (+ reuse sends nothing), paid-trio across webhook path, delivery/ship/deliver mails, cancel-trio, refund mails + refund-failure silence, online-canceling (visible-through-period, fired only on first `canceling` transition — repeat `subscription.updated` on an already-canceling sub does NOT re-mail), online-canceled (hidden, mails even without a prior canceling event), duplicate + cash-ignore.
- [x] 5.2 Manual smoke with console backend: buy → reserved mails on console; Stripe CLI `checkout.session.completed` → paid trio; `customer.subscription.updated` (cancel_at_period_end) → online-canceling pair; `customer.subscription.deleted` → online-canceled pair; admin ship/deliver/release actions.
- [x] 5.3 Update `emails-track.md` matrix with the 8 new rows (trigger → subjects → Validated=true) and note the reserved/cancelled noise follow-up.