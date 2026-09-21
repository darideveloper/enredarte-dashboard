# Emails Track

All mail is sent from `subscriptions/services/notifications.py` via `EmailMultiAlternatives`
(TXT + HTML alternatives, Spanish-only, best-effort: a mail failure never rolls back a state
change and never turns a webhook 200 into a 500). Use `notifications.send_best_effort(...)`
at every firing site.

The audience of each mail is chosen only from addresses the flow already holds:

- `to=[order.buyer_email]` — the **buyer** (captured at buy time / from the Stripe Checkout session).
- `to=[order.artwork.artist.email]` — the **artist** who owns the sold work, mailed only for the
  "buyer + admin + artist" triggers (paid / delivery-complete / cancelled / refunded); skipped with
  a logged warning when blank.
- `to=[artist.email]` — the artist is the **customer** for subscription flows (cash + online).
- `to=EMAILS_NOTIFICATIONS` — the **admin** list, skipped with a logged warning when empty
  (`[Enredarte]`-prefixed subject, admin change-page link included).

## Current — cash subscriptions (7 senders, live)

| Trigger | Audience | Subjects (per audience) | Templates | Validated |
|---|---|---|---|---|
| Admin "Marcar como efectivo" (`artworks/admin.py`) → `send_cash_pending` | artist + admin | "Tu registro de pago en efectivo está pendiente" / "[Enredarte] Artista marcado como efectivo — {artista}" | `cash_pending.{txt,html}` + `cash_pending_admin.*` | true |
| Admin "Confirmar pago" → `send_cash_active` | artist + admin | "Tu pago en efectivo fue confirmado" / "[Enredarte] Pago en efectivo confirmado — {artista}" | `cash_active.*` + `cash_active_admin.*` | true |
| Admin "Cancelar efectivo" → `send_cash_canceled` | artist + admin | "Tu suscripción en efectivo fue cancelada" / "[Enredarte] Suscripción en efectivo cancelada — {artista}" | `cash_canceled.*` + `cash_canceled_admin.*` | true |
| Cron `check_cash_renewals.py` (renew in 3d) → `send_cash_reminder` | artist + admin | "Tu suscripción vence en 3 días" / "[Enredarte] Suscripción por vencer — {artista}" | `cash_reminder.*` + `cash_reminder_admin.*` | true |
| Cron `:65` (renew today) → `send_cash_duetoday` | artist + admin | "Tu suscripción vence hoy" / "[Enredarte] Suscripción vence hoy — {artista}" | `cash_duetoday.*` + `cash_duetoday_admin.*` | true |
| Cron `:68` (past renew → `past_due`) → `send_cash_overdue` | artist + admin | "Tu pago está vencido" / "[Enredarte] Pago vencido — {artista}" | `cash_overdue.*` + `cash_overdue_admin.*` | true |
| Cron `:75` (past grace → `canceled`) → `send_cash_deactivated` | artist + admin | "Tu suscripción fue desactivada por falta de pago" / "[Enredarte] Artista desactivado por no renovar — {artista}" | `cash_deactivated.*` + `cash_deactivated_admin.*` | true |

## Current — artwork sales (change `expand-email-notifications` implemented, 7 senders)

| Trigger (firing point) | Audience | Subjects (per audience) | Templates | Validated |
|---|---|---|---|---|
| Sale reserved — `buy` endpoint reserves, order `pending_payment`; fires post-commit, only on a fresh reservation (same-buyer reuse `200` sends nothing) → `send_sale_reserved` | buyer + admin | "Tu compra está reservada: completa tu pago" / "[Enredarte] Nueva reserva — {artwork} ({order})" | `sale_reserved_buyer.*` + `sale_reserved_admin.*` | true |
| Sale paid — order `pending_payment → paid_pending_data` (artwork `sold`); any of: `checkout.session.completed` (`payment_status=paid`), `async_payment_succeeded`, `OrderSummaryView` fallback, lazy reconcile, `sync_orders_from_stripe`. Fires only when the transition returns `True` (no double-mail across races); webhook paths via `transaction.on_commit` → `send_sale_paid` | buyer + admin + artist | "Tu pago fue confirmado" / "Tu obra {title} se vendió" / "[Enredarte] Venta pagada — {artwork} ({order})" | `sale_paid_{buyer,artist,admin}.*` | true |
| Delivery complete — `POST orders/{slug}/delivery/` → `data_complete`; only on real transition → `send_sale_delivery_complete` | buyer + admin + artist | "Recibimos tus datos de entrega" / "Datos de entrega listos para {title}" / "[Enredarte] Datos de entrega — {artwork} ({order})" (admin carries full buyer address; artist body states address-sharing purpose, no payment ids) | `sale_delivery_complete_{buyer,artist,admin}.*` | true |
| Order shipped — admin "Marcar enviada" `data_complete → shipped`; per actually-changed row after bulk `.update()` → `send_sale_shipped` | buyer + admin | "Tu obra va en camino" / "[Enredarte] Pedido enviado — {artwork} ({order})" | `sale_shipped_{buyer,admin}.*` | true |
| Order delivered — admin "Marcar entregada" `shipped → delivered`; per actually-changed row → `send_sale_delivered` | buyer + admin | "Tu obra fue entregada ¡gracias por tu compra!" / "[Enredarte] Pedido entregado — {artwork} ({order})" | `sale_delivered_{buyer,admin}.*` | true |
| Order cancelled — order `pending_payment → cancelled` (artwork `available`); any of: `checkout.session.expired`, `async_payment_failed`, `release_expired_orders`, `sync_orders_from_stripe`, admin "Liberar reserva", lazy reconcile cancel. Fires only on a real transition → `send_sale_cancelled` | buyer + admin + artist | "Tu pago no se completó" / "La reserva de {title} se liberó" / "[Enredarte] Reserva cancelada — {artwork} ({order})" | `sale_cancelled_{buyer,artist,admin}.*` | true |
| Order refunded — double-sale backstop marks `refunded` + automatic Stripe refund succeeds (webhook + reconcile). No mail if `create_refund` raises (500 → Stripe retry) → `send_sale_refunded(order, refund_id=...)` | buyer + admin + artist | "Tu reembolso está en camino" / "Aviso de doble pago en {title}" / "[Enredarte] Reembolso por doble venta — {artwork} ({order})" (admin carries payment-intent + refund ids) | `sale_refunded_{buyer,artist,admin}.*` | true |

## Current — online Stripe subscriptions (change `expand-email-notifications` implemented, 2 senders)

| Trigger (firing point) | Audience | Subjects (per audience) | Templates | Validated |
|---|---|---|---|---|
| Online cancel requested — `customer.subscription.updated` with `cancel_at_period_end=true` → status `canceling` (artist **stays visible** through period end). **Transition-gated**: fires only when the previous stored status was not already `canceling`, so spurious re-updates do not re-mail → `send_online_canceling` | artist + admin | "Tu suscripción en línea será cancelada" (visible until period end) / "[Enredarte] Suscripción en línea en cancelación — {artista}" | `online_canceling.*` + `online_canceling_admin.*` | true |
| Online cancel ended — `customer.subscription.deleted` → status `canceled` (artist hidden via `compute_is_active`); mails even if no prior `canceling` was observed → `send_online_canceled` | artist + admin | "Tu suscripción en línea fue cancelada" (no longer visible) / "[Enredarte] Suscripción en línea cancelada — {artista}" | `online_canceled.*` + `online_canceled_admin.*` | true |

## Notes

- Artist mails for artwork sales appear only for paid / delivery-complete / cancelled / refunded
  (operator decision during exploration: reserved, shipped, delivered are buyer + admin only).
- Online cancellation is two-phase by operator decision: `canceling` (still visible) and `canceled`
  (hidden) each mail once.
- All webhook-originated sends ride `transaction.on_commit` so mail leaves only after commit and a
  mail failure keeps the webhook 200; cash/admin/cron paths send directly, best-effort.
- Known follow-up: reserved + cancelled mail pairs on abandoned checkouts can add mail volume;
  a digest/suppression option is deferred (see `expand-email-notifications` design.md).
- Automated coverage: `SaleEmailNotificationsTest`, `OnlineEmailNotificationsTest`,
  `ArtworkOrderWebhookEmailTest` (subscriptions/artworks test suites). `Validated=true` reflects
  automated tests; a manual console-backend smoke run (task 5.2) is still pending operator execution.