## 1. Brand foundation

- [x] 1.1 Create `core/mail_branding.py` with `BRAND` dict (paper `#F2EDE4`, ink `#1A1A1A`, crimson `#C41E3A`, muted `#8A8478`, border `#E0DDD8`, banner `#EAE4D8`, description `#7A7568`), `WORDMARK = "ENREDARTE"`, `FOOTER_CONTACT = "info@enredarte.com"`, as a plain module with a docstring (no Django model involved).
- [x] 1.2 Inject brand/footer context in `core/mail_utils.py:send_audience` (merge `brand`, `footer_contact`, `year` into `ctx`) and in `subscriptions/services/notifications.py:_context` (cash senders bypass the shared renderer, so both paths inject); base/partials use `|default` fallbacks so direct `render_to_string` in tests still resolves.
- [x] 1.3 Create `project/templates/email/base.html` with paper page, white sharp card (`0px`, 1px border, no shadow, 600px max), `eyebrow` / `title` / `body` / `cta` / `footer_note` blocks and inline-safe CSS; every brand/footer variable uses `|default` fallbacks so direct `render_to_string` without sender context still renders.
- [x] 1.4 Create `project/templates/email/_wordmark.html` (Georgia uppercase tracked `ENREDARTE` + crimson rule, no `<img>`) and `project/templates/email/_footer.html` (reply-hint + `© {year} Enredarte · info@enredarte.com`, `#E0DDD8` rule).

## 2. Migrate subscription HTML (18 files)

- [x] 2.1 Migrate cash artist bodies (`cash_{pending,active,canceled,reminder,duetoday,overdue,deactivated}.html`) to `{% extends "email/base.html" %}`, moving copy into `body` block with eyebrow + serif title, deleting per-file `<style>`.
- [x] 2.2 Migrate cash admin bodies (`cash_*_admin.html`, 7 files) to the base shell with operational copy preserved plus admin change-page link.
- [x] 2.3 Migrate online pairs (`online_{canceling,canceled}{,_admin}.html`, 4 files) with visibility-consequence copy unchanged.
- [x] 2.4 Verify each migrated subscription HTML renders with `brand` tokens and footer; confirm no `#1d3a2f`, `border-radius: 16px`, `<style>`, or `<img>` remains (`rg` check).

## 3. Migrate artwork-sale HTML (18 files)

- [x] 3.1 Migrate `sale_reserved_{buyer,admin}.html`: buyer keeps ES+EN sections with repeated eyebrow/title and crimson block checkout CTA (`checkout_url`); admin keeps buyer/artwork/amount/session-id + order admin link.
- [x] 3.2 Migrate `sale_paid_{buyer,artist,admin}.html`: buyer bilingual receipt + delivery-form instructions; artist title/amount/consequence; admin buyer/ids/admin link.
- [x] 3.3 Migrate `sale_delivery_complete_{buyer,artist,admin}.html`: buyer bilingual confirmation; artist address-purpose line without Stripe ids; admin full address + contacts + link.
- [x] 3.4 Migrate `sale_shipped/delivered_{buyer,admin}.html` (4 files): bilingual buyer bodies, admin state + link, no artist mail.
- [x] 3.5 Migrate `sale_cancelled/refunded_{buyer,artist,admin}.html` (6 files): bilingual buyer bodies; artist release/conflict copy; admin reason/ids/links (refund carries payment-intent + refund ids).
- [x] 3.6 Verify all sale HTML extend the base, contain `ENREDARTE` wordmark + `info@enredarte.com`, and contain no `#1d3a2f`, `border-radius: 16px`, `<style>`, `<img>`, or social URLs (`rg` check).

## 4. TXT sync + verification

- [x] 4.1 Diff each `.txt` against its migrated `.html` body to confirm same facts/links/amounts (no copy change beyond wrapper; bilingual sections intact).
- [x] 4.2 Run targeted mail suites: `venv/bin/python manage.py test subscriptions artworks core --verbosity=2` (covers `SaleEmailNotificationsTest`, `OnlineEmailNotificationsTest`, `ArtworkOrderWebhookEmailTest`, cash mail tests); fix regressions.
- [x] 4.3 Console-backend visual smoke: trigger one cash, one sale, one online mail via Django shell/admin and inspect rendered HTML for paper/sharp/serif/crimson/wordmark/minimal-footer; confirm no `example.com` or green literals leak.
- [x] 4.4 Update `emails-track.md` branding note (shell + tokens location, wordmark/footer convention).
