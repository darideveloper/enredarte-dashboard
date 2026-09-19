## Context

Each `Artist` has at most one `ArtistSubscription` (1:1), Stripe is the source of truth, and `Artist.is_active` (public-site visibility) derives from `compute_is_active()` (`subscriptions/services/subscription_state.py`). All operator controls are Unfold `actions_detail` header buttons on the Artist change page (`artworks/admin.py:318`), gated by `has_<action>_permission` methods wired via `@action(permissions=[...])`. Webhooks at `POST /webhooks/stripe/` mirror Stripe state idempotently (`StripeEvent.event_id` unique + single `transaction.atomic()`).

No email infrastructure exists: zero `EMAIL_*` in `project/settings.py`, zero `EMAIL_*` in `.env.*.example`, zero mail sends in code. `docs/django-project-setup.md:385-396` documents the SMTP block to add when email is first needed. This change is that moment.

Stakeholders: operators (admin staff managing artists), artists (cash payers receiving receipts), admins (notification recipients).

## Goals / Non-Goals

**Goals:**
- Operators onboard cash payers fully from the admin with an auditable state trail (pending → active → canceled).
- Cash artists get correct public visibility (hidden → visible indefinitely → hidden) through the existing `compute_is_active()` path.
- Stripe and cash paths never interfere (buttons, webhooks, sync, portal).
- Artist + admin receive HTML emails on every cash transition via a reusable mailer convention.
- Zero new dependencies; Django test runner stays canonical.

**Non-Goals:**
- No per-payment amounts, renewal ledger, or expiry/grace for cash (indefinite until cancelled per explore decision).
- No `past_due`/`canceling` states for cash (no invoices exist).
- No new status enum values, badge colors, or public API changes.
- No background jobs, cron, or async mail queue (synchronous send; failure degrades to warning).
- No email provider SDK (stdlib SMTP only).

## Decisions

### D1: `payment_method` discriminator + reused `Status` (not new states)
Add `ArtistSubscription.payment_method = CharField(choices=[online, cash], default=online)`. Cash reuses `pending/active/canceled`; `compute_is_active()` works unchanged (pending→False, active→True, canceled→False).
- Alternative: new statuses (`cash_pending`, `cash_active`). Rejected: ripples into badges (`admin_helpers.py`), list filters, `map_stripe_status`, specs, and every `status ==` check for zero behavioral gain.
- Alternative: separate `CashSubscription` model. Rejected: breaks the 1:1 invariant, duplicates visibility logic, complicates the admin inline.

### D2: Three server-side header buttons (not form fields)
`marcar-efectivo`, `confirmar-pago-efectivo`, `cancelar-efectivo` as Unfold `actions_detail` with `has_*_permission` gates, mirroring `generate_link` etc. Each transition runs validate → flip → `compute_is_active` → save → notify → message + 302 in one request.
- Alternative: editable `payment_method`/`status` form fields. Rejected: declares state without side effects; half-saved forms could desync `status`/`is_active`; emails would need fragile `save()` hooks.
- Visibility matrix enforced at render AND execution: hidden buttons refuse direct URLs at the Unfold permission boundary (403, verified in tests); methods keep defensive Spanish guards for defense in depth.

```
No sub / cash-canceled ..... Marcar + (online) Generar
Cash pending ................ Confirmar + Cancelar        (all Stripe hidden)
Cash active ................. Cancelar only               (all Stripe hidden)
Online (any link) ........... Stripe set only             (all cash hidden)
```

### D3: Stripe-path isolation via guards (not data cleanup)
- `upsert_from_stripe()`: return `None` (log + ignore) when the matched row is cash — webhooks can never flip cash.
- `sync_from_stripe` / `open_portal`: refuse cash rows early with an explanatory message (buttons already hidden; this covers direct URLs).
- `generate/regenerate_link`: refuse when a cash `pending`/`active` row exists (prevents dual-path rows). `stripe_customer_id`/`stripe_subscription_id` stay empty on cash rows; `raw_state` stores `{"cash": true, ...}` audit instead of a Stripe object.
- Alternative: detach/clear Stripe IDs on cash mark. Rejected: destroys audit trail of a prior online history.

### D4: Central stdlib mailer, two sends per transition
New `subscriptions/services/notifications.py` — the only module allowed to send mail — with `send_cash_pending/active/canceled(artist, actor)`. Each sends twice: artist receipt (`to=[Artist.email]`) + admin notice (`to=EMAILS_NOTIFICATIONS`, subject `[Enredarte] …`). `EmailMultiAlternatives` with TXT + HTML alternatives. Exact Spanish subjects are pinned in the email-notifications spec; the English `[Admin]` prefix is deliberately not used.
- Alternative: single send with CC. Rejected: leaks internal addresses to artists; prevents per-audience tone/subject.
- Alternative: one shared body for both audiences. Rejected: the artist greeting ("Hola, …") and reply line read wrong in an operator inbox; per-audience pairs cost 6 small files and keep each message fit for purpose.
- Alternative: provider SDK (Resend/SES API). Rejected: SMTP covers current volume; new dep + credential shape for no gain (YAGNI ladder).
- Backend resolution: `console` in dev/test (zero setup, content verifiable in runserver log), `smtp` in prod, `locmem` under tests via `outbox`.

```
Admin action → flip+save → notifier → render html/txt → Email #1 (artist) → Email #2 (admins)
Email failure → logger.exception + messages.warning; state stays flipped (never rollback).
```

### D5: Template convention `cash_<transition>[ _admin].{html,txt}`
Artist templates (`cash_{pending,active,canceled}`) are fully in Spanish matching the admin language (greeting + transition explanation + visibility consequence + contact line per the spec). Admin notices use dedicated `cash_{kind}_admin` templates with an operational tone (artist name + email, transition + visibility consequence, acting operator, direct admin change-page link) and a distinct `[Enredarte] …` subject — the artist greeting is never sent to admins. Future emails follow the same per-audience-pair rule — no new plumbing.

## Risks / Trade-offs

- [Risk] SMTP down at confirm-time → artist pays cash but gets no receipt → Mitigation: state still flips; warning message + log; operator resends manually (documented runbook step).
- [Risk] Operator marks cash on an artist with an active Stripe subscription → double-billing confusion → Mitigation: `Marcar` refuses when an online active/past_due/canceling row exists; message directs to cancel in Stripe first.
- [Risk] Cash stays `active` forever (indefinite) even if artist stops paying → Mitigation: accepted per explore decision; `Cancelar efectivo` is the off-switch; a future renewal-ledger change can add expiry without touching this design.
- [Risk] Webhook for a recycled `cus_xxx` (cash artist previously online) arrives → Mitigation: cash guard ignores it; logged for audit.
- [Trade-off] Synchronous send adds latency to the admin click (~1s SMTP) → accepted; no Celery/queue in this codebase, and failure semantics stay simple.
- [Trade-off] `EMAILS_NOTIFICATIONS` misconfigured (empty) → admin emails silently skipped → Mitigation: notifier logs warning when list is empty; settings check documents the var as required in prod.

## Migration Plan

1. Deploy code + `EMAIL_*`/`EMAILS_NOTIFICATIONS` env (prod SMTP creds; dev stays console). No `manage.py` behavior change until migration runs.
2. Run migration: adds `payment_method` (default `online`) — all existing rows stay online; zero data rewrite; backwards compatible.
3. Verify: Django check, targeted test run (`subscriptions`, `artworks` admin action tests), send a console-backend cash transition in dev, confirm `outbox` assertions pass.
4. Rollback: revert code + migrate back (`migrate subscriptions <prev>`); cash rows created in the window keep their data but are inert under old code (unknown column is dropped, statuses remain readable). SMTP env vars are harmless leftovers.

## Open Questions

- None blocking. Resolved in explore: full manual states (not auto), indefinite validity, emails on all three transitions, new `EMAILS_NOTIFICATIONS` list + fresh SMTP creds.
