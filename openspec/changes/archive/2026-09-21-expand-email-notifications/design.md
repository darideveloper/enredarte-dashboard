## Context

Cash subscriptions already mail artist + admin on all 7 transitions via the single mailer `subscriptions/services/notifications.py` (`EmailMultiAlternatives` TXT+HTML, Spanish, best-effort). Artwork sales (`ArtworkOrder` lifecycle in `artworks/`: buy → paid → delivery → shipped → delivered, with cancelled/refunded exits) and online Stripe subscriptions (`subscriptions/webhooks.py`) send zero mail. The buy/webhook/reconcile/summary race paths all converge on two shared transitions (`apply_paid_transition`, `cancel_order` in `artworks/services.py`), which is where idempotent mail hooks belong. No new settings or models are needed: `EMAIL_FROM`, `EMAILS_NOTIFICATIONS`, `HOST` (admin links) and `PUBLIC_SITE_URL` (buyer links) already exist.

## Goals / Non-Goals

**Goals:**
- Buyer + admin (+ artist where decided) receive a Spanish receipt/notice on each of the 8 triggers, with the same TXT+HTML, best-effort, skip-and-log conventions as cash mails.
- Paid mails fire exactly once per order even though 5 code paths can apply the paid transition (webhook completed, async-succeeded, summary race fallback, lazy reconcile, sync command).
- Webhook-originated mails never turn a 200 into a 500 and never send phantom mail for rolled-back transactions.
- Approach A: everything lives in `notifications.py` (no new mailer module), templates follow the existing per-audience pair convention.

**Non-Goals:**
- No digest/queue/Celery: synchronous sends with `transaction.on_commit` for webhook paths and direct send for request/admin/cron paths (volume is a few mails/day; reserved/cancelled noise is accepted, see risks).
- No buyer-reminder before 30-min expiry, no online renewal/success mails, no blog mails, no template redesign of existing cash mails.
- No Stripe Dashboard mail changes; Django mails are the only new surface.

## Decisions

**D1 — Approach A: extend `notifications.py`, no new module.**
Why: single-mailer invariant is spec'd (`email-notifications`) and tested; reviewers know where mail lives; diff is additive. Alternative (new `sales_notifications.py`) was rejected: it splits conventions and doubles the empty-list/failure patterns to keep in sync.

**D2 — Generic triple-send helper `_send_sale(kind, order, ...)` / `_send_online(kind, artist/sub, ...)`.**
Each audience gets its own subject + template pair and is sent as a separate `EmailMultiAlternatives` (never CC): buyer (`sale_{kind}_buyer`), artist (`sale_{kind}_artist`, only for paid/delivery_complete/cancelled/refunded), admin (`sale_{kind}_admin`), online (`online_canceling` + `online_canceling_admin` for the request phase; `online_canceled` + `online_canceled_admin` for the final phase). Missing address (blank buyer/artist email, empty `EMAILS_NOTIFICATIONS`) → skip that audience + `logger.warning`, same as cash today. Shared context: `{order, artwork, artwork_title, artist, artist_name, buyer_email, amount, currency, host, admin_url, checkout_url (reserved only), renew/paid dates}`.

**D3 — Fire on a genuine transition, per firing mechanism.**
The guiding rule is "mail only when a real state change happens". Where a transition helper exists, gate on its return value: `apply_paid_transition` / `cancel_order` already return `True` only on a real change, so every paid site (`_apply_artwork_paid`, `_apply_reconciled_paid`, `OrderSummaryView`, `sync_orders_from_stripe`) sends `send_sale_paid` only when the call returns `True`, and webhook/reconcile/`release_expired_orders` cancel sites only when `cancel_order` returns `True`. This makes the webhook-vs-summary race and lazy-reconcile-vs-webhook overlaps idempotent for free. Where the site mutates directly (admin `marcar_enviada`/`marcar_entregada` use bulk `queryset.filter(...).update(...)`, and `liberar_reserva` sets each row in a loop), there is no helper return value: the site SHALL re-read the actually-changed rows after mutation and send one mail per row that truly transitioned (bulk `.update()` returns the changed-row count; `liberar_reserva` knows per-row success from its `PENDING_PAYMENT` guard). Alternative (dedupe table/flag on order) was rejected as extra state for a property the transitions already express.

**D4 — Best-effort everywhere, with `on_commit` on webhook paths.**
Request/admin/cron paths: try/except around sends, log + continue (admin actions show the existing `messages.warning`). Webhook paths run inside the `StripeEvent` atomic block, so sends are registered via `transaction.on_commit(...)` — mail leaves only after the state commits, and a mail exception is caught inside the callback (log only, handler still returns 200). This avoids both phantom mail on rollback and Stripe retry storms from a 500. Alternative (send inline in handler) was rejected for exactly those two failure modes.

**D5 — `buy` sends reserved mail after commit, outside the atomic block.**
The reservation + order + Stripe session persist inside `transaction.atomic`; the two reserved mails (buyer with `checkout_url`, admin with buyer/artwork/session) send after the block succeeds, wrapped in try/except so SMTP slowness/failure can never turn a `201` into a `502`. Same-buyer reuse (`200` same URL) re-sends nothing (no new transition). Alternative (Celery/outbox) rejected: no worker infra exists; volume does not justify it.

**D6 — Spanish subjects, `[Enredarte]` admin prefix (exact strings in specs).**
Buyer subjects are action-oriented ("Tu compra…", "Tu pedido…", "Tu reembolso…"); artist subjects name the work ("Tu obra … se vendió"); admin subjects carry order slug + state. Bodies: buyer = what happened + what to do next (link to success page / delivery form / support reply line); artist = work title + amount + visibility/state consequence + contact line (delivery-complete states the address-sharing reason explicitly); admin = buyer + artwork + artist + amount/currency + Stripe session/payment-intent ids + direct admin change-page link.

**D7 — No new settings or models.**
Reuse `EMAIL_FROM`, `EMAILS_NOTIFICATIONS`, `HOST`, `PUBLIC_SITE_URL`. No migration; deploy is code + templates; rollback is revert.

**D8 — Online cancellation notifies both phases, transition-gated.**
Stripe online cancellation is two-phase. `subscription.updated` with `cancel_at_period_end=true` maps to `CANCELING` (artist **still visible** through period end); `subscription.deleted` maps to `CANCELED` (artist hidden). Per operator decision, both moments mail artist + admin: `send_online_canceling` on the `CANCELING` transition (body: "visible until period end") and `send_online_canceled` on the `CANCELED` transition (body: "no longer visible"). Because `subscription.updated` fires on every Stripe subscription update (renews, payment-method changes) and `map_stripe_status` re-derives `CANCELING` whenever `cancel_at_period_end` is set, the `send_online_canceling` email is **transition-gated**: it SHALL send only when the previous stored status was NOT already `canceling` (i.e. a genuine transition into cancellation), so spurious re-updates of an already-canceling row re-derive the status but do not re-mail. The `CANCELED` mail is gated on `subscription.deleted` (fires once in practice, idempotent via `StripeEvent`). Whichever event is observed first mails its phase; the other phase mail only fires if its own transition is later observed. Both fire via `transaction.on_commit` in the webhook block. Cash rows stay ignored by the existing cash guard.

## Risks / Trade-offs

- [Risk] Reserved + cancelled pair on every abandoned checkout → admin/buyer mail noise → Mitigation: accepted for v1 (traffic is a few buys/day; throttle caps at 20 buys/hour); follow-up task records a digest/suppression option if noise materializes. Buyer-reserved mail is the price of delivering the checkout link by mail.
- [Risk] Paid mail missed if a future transition path forgets the return-value check → Mitigation: spec scenario per firing path; tests assert one mail per paid order across webhook + summary-race + sync-command runs.
- [Risk] `on_commit` callbacks never run in tests wrapped in outer atomics → Mitigation: tests use `captureOnCommitCallbacks` (Django 4+) or call senders directly for content asserts and separately assert registration.
- [Risk] Buyer address shared with artist on delivery-complete → Mitigation: intentional per operator; template states purpose ("para coordinar la entrega") and includes only the delivery fields, no payment ids.
- [Risk] SMTP latency inside `buy` request (post-commit send blocks response) → Mitigation: sends are small/local Brevo SMTP; failure path is fast-fail + warn; async queue explicitly deferred to a follow-up if p99 suffers.
- [Risk] Webhook retry after successful mail (e.g. crash after `on_commit` ran) → Mitigation: `StripeEvent` idempotency means the handler never re-runs for the same `event_id`, so the mail callback registers at most once per event.
- [Risk] Repeated `subscription.updated` for an already-canceling sub re-derives `CANCELING` on every Stripe update → Mitigation: the `send_online_canceling` mail is transition-gated (only when the previous status was not already `canceling`), so only the first transition into cancellation mails.
