## 1. Data model

- [x] 1.1 Add `payment_method` (`online`/`cash`, default `online`, verbose_name + help_text) to `ArtistSubscription` with migration; verify existing rows read as `online`.
- [x] 1.2 Guard `upsert_from_stripe()` to return `None` (log + ignore) when the matched row is cash; cover with a unit test.

## 2. Email infrastructure

- [x] 2.1 Add `EMAIL_*` + `EMAILS_NOTIFICATIONS` settings block (console default in dev/test, SMTP via env) and document vars in `.env.dev.example` / `.env.prod.example`.
- [x] 2.2 Create `subscriptions/services/notifications.py` with `send_cash_pending/active/canceled` (two `EmailMultiAlternatives` sends each, exact Spanish subjects from the spec, empty-list warning).
- [x] 2.3 Create paired artist templates `cash_{pending,active,canceled}.html` + `.txt` and paired admin templates `cash_{pending,active,canceled}_admin.html` + `.txt` under `subscriptions/templates/subscriptions/email/` with shared context (`artist`, `plan`, `actor`, host); fully Spanish copy with the spec's required elements per audience (artist: greeting, transition, visibility consequence, contact line; admin: name+email, transition, operator, admin link).
- [x] 2.4 Add mailer tests via `django.core.mail.outbox`: artist + admin recipients, HTML/TXT alternatives, exact Spanish subjects + required body elements, empty-list skip, failure-never-blocks (mock SMTP raise, state still flips).

## 3. Cash admin actions

- [x] 3.1 Add `marcar-efectivo`, `confirmar-pago-efectivo`, `cancelar-efectivo` actions + `has_*_permission` gates to `ArtistAdmin` (transitions, `compute_is_active`, exact Spanish messages from the spec, email calls with try/except → warning).
- [x] 3.2 Gate the four Stripe actions + direct-URL refusal on cash rows (`generate/regenerate/portal/sync` permission guards).
- [x] 3.3 Refuse `generate/regenerate_link` when a cash `pending`/`active` row exists (no dual-path rows).
- [x] 3.4 Add admin action tests: each transition flips status/`is_active` + sends 2 emails; exact Spanish action/refusal messages from the specs; idempotent double-confirm sends nothing; cross-path URLs refused; Stripe buttons hidden on cash rows.

## 4. Webhook isolation

- [x] 4.1 Route all subscription/invoice handlers through the cash guard (record event, log ignore, no mutation); add webhook test posting a subscription event against a cash row.

## 5. Verification

- [x] 5.1 Run `venv/bin/python manage.py check` + full `subscriptions` and `artworks` admin test suites (`venv/bin/python manage.py test subscriptions artworks --verbosity=2`).
- [x] 5.2 Manual pass in dev (console backend): mark → confirm → cancel a test artist; verify visibility flips, console prints 6 emails, Stripe buttons show/hide per matrix.
- [x] 5.3 Set prod `EMAIL_*`/`EMAILS_NOTIFICATIONS` env and confirm docs (`django-project-setup.md` email note, `stripe-subscriptions.md` admin controls) updated if they describe the button set.
