## Why

All 36 transactional HTML emails copy-paste the same inline `<style>` block (cream `#faf7f2` page, forest-green `#1d3a2f` headings, 16px rounded card, sans-only type) with no shared base, no logo, and no connection to the landing's Gallery Salon system (`DESIGN.md`: paper `#F2EDE4`, ink `#1A1A1A`, crimson `#C41E3A`, Georgia serif display, sharp `rounded-none`, tracked uppercase eyebrows). Every re-brand touch means editing 36 files, and today's green/rounded look contradicts the public site buyers and artists see.

## What Changes

- Add one shared HTML shell for all transactional mail: `project/templates/email/base.html` (header wordmark, eyebrow + serif title slots, body block, CTA + minimal-footer slots), owned by `core`.
- Add one token source `core/mail_branding.py` mirroring the landing palette/typography (paper, ink, crimson, muted, border) plus footer contact (`info@enredarte.com`), so colors/fonts never live in 36 places again.
- Migrate all 18 artwork-sale + 18 subscription HTML templates to `{% extends "email/base.html" %}`, deleting per-file `<style>`/`<head>` boilerplate; bodies keep current copy, subjects, audiences, and firing rules unchanged.
- Re-brand to landing tokens: paper page, white sharp card (`0px`, 1px `#E0DDD8` border, no shadow — white card locked over full-paper for dark-mode contrast, see design §4), Georgia serif titles with crimson uppercase eyebrow, ink body, crimson sharp CTAs (`15px 32px`, uppercase, tracked), muted footer with reply-hint + `© Enredarte · info@enredarte.com`.
- Header uses a text wordmark (`ENREDARTE`, Georgia, tracked, ink + crimson rule) — no image, no absolute-URL hosting, dark-mode safe.
- TXT companions unchanged in content; only verified in sync with HTML bodies.

## Capabilities

### New Capabilities
- `email-branding`: centralized email visual system — shared base shell, landing token source, wordmark header, CTA and minimal-footer blocks; governs HTML structure/styling of all transactional mail without changing audiences, subjects, or firing rules.

### Modified Capabilities
- None. `email-notifications`, `sales-emails`, `subscription-emails` requirements (audiences, subjects, per-audience bodies, best-effort/on_commit semantics, TXT+HTML pairing) stay unchanged; this change only restyles the HTML shell around the same bodies.

## Impact

- Affected: `core/mail_utils.py` (context injection only), new `core/mail_branding.py`, new `project/templates/email/base.html` (+ header/footer includes), 36 `.html` files under `artworks/templates/artworks/email/` and `subscriptions/templates/subscriptions/email/`.
- No DB migrations, no new dependencies, no settings/env changes, no subject/audience/firing-rule changes.
- Test surface: `SaleEmailNotificationsTest`, `OnlineEmailNotificationsTest`, `ArtworkOrderWebhookEmailTest` and cash mail tests must stay green; visual check via console-backend smoke run.
