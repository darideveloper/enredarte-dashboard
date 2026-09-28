## Context

Today every transactional HTML mail (`artworks/templates/artworks/email/sale_*_{buyer,artist,admin}.html`, 18 files; `subscriptions/templates/subscriptions/email/{cash_*,online_*}*.html`, 18 files) embeds its own full `<head>` + inline `<style>`: cream `#faf7f2` page, forest-green `#1d3a2f` headings, 16px rounded `.card` with shadow, sans-only type, no shared include (`grep extends|include|static|<img` over both dirs → 0 hits, no `email/base*` exists). Rendering flows through `core/mail_utils.py:34-47` `send_audience(subject, ctx, template_base, recipients)` → `render_to_string(f"{base}.txt"/".html")` → `EmailMultiAlternatives` + `attach_alternative`. TXT companions are unstyled plaintext and stay in sync manually.

The landing (`/mnt/hd/develop/astro/enredarte-landing/DESIGN.md` + `src/styles/global.css:4-18`) defines the Gallery Salon system this must follow: paper `#F2EDE4`, ink `#1A1A1A`, crimson `#C41E3A`, muted `#8A8478`, border `#E0DDD8`, banner `#EAE4D8`; display `Georgia, 'Times New Roman', serif`, body/label system sans; sharp `rounded-none` geometry; flat-by-default (no resting shadows); uppercase tracked eyebrows (`Headline.astro`: `10px`, `0.22em`, crimson); primary CTA (`Btn.astro:primary`: crimson block, paper text, sharp, `15px 32px`, uppercase `0.1em`). Contact source of truth is `src/data/site-config.ts:15-18` (`info@enredarte.com`). Only repo image is dashboard `static/favicon.png` (admin Unfold icon, never used in mail).

Explore decisions locked with the operator: text wordmark (no image), sharp cards, full crimson accents, minimal footer.

## Goals / Non-Goals

**Goals:**
- One HTML shell + one token source for all 36 mails; per-file `<style>` deleted.
- Visual parity with landing tokens above (paper/ink/crimson, serif titles + eyebrow, sharp flat cards, crimson block CTAs, minimal footer).
- Zero change to audiences, subjects, firing rules, best-effort/`on_commit` semantics, or TXT content.
- All existing mail tests stay green; console-backend visual smoke passes.

**Non-Goals:**
- No copy rewrite beyond wrapping bodies in the new shell (bilingual ES+EN buyer bodies keep both sections, divider restyled only).
- No logo image pipeline (no S3/static hosting, no absolute-URL images).
- No full footer (no socials/legal matrix), no dark-mode-specific template fork, no MJML/premailer dependency.
- No settings/env changes, no migrations.

## Decisions

### 1. Shared shell: `templates/email/base.html` + header/footer includes, owned by `core`
`core` already owns `mail_utils.py`; the shell lives next to it conceptually (`project/templates/email/base.html` so both `artworks/email/*` and `subscriptions/email/*` namespaces can `{% extends "email/base.html" %}`). Blocks: `eyebrow`, `title`, `body`, `cta`, `footer_note`. Header/footer as `{% include %}` partials so a footer tweak touches one file. Per-mail templates keep only body content + block overrides.
- Alternative (per-namespace base duplicated in each app): rejected — recreates the two-sources drift this change kills.
- Alternative (Python string builder emitting HTML): rejected — breaks Django template override/test conventions (`render_to_string` assertions in `SaleEmailNotificationsTest` etc.).

### 2. Tokens: `core/mail_branding.py` dict, injected via `send_audience`
Single `BRAND = {paper, card, ink, crimson, muted, border, banner_bg, ...}` + `FOOTER_CONTACT = "info@enredarte.com"` + `WORDMARK = "ENREDARTE"`, merged into every `send_audience` context. Templates reference `{{ brand.paper }}` etc., never literals. Mirrors landing `global.css:9-17` values verbatim.
- Alternative (hardcode hex in base.html only): rejected — tokens then still untraceable from Python/tests; dict keeps one grep-able source.
- Alternative (CSS file / `{% static %}`): rejected — email clients strip external CSS; inline `<style>` in base head is the only reliable channel.

### 3. Wordmark as styled text, not image
Header: `ENREDARTE` in Georgia, uppercase, `0.18-0.22em` tracking, ink, with a short crimson rule underneath (echoes `Headline.astro` + `CardInfo` accent bar). No `<img>`, no hosted asset.
- Rationale: kills the hardest email problem (absolute image URLs, Outlook blocking, S3/CDN wiring, `PUBLIC_SITE_URL` vs `HOST` confusion) and survives dark-mode inversion. Landing recognizability comes from type + crimson, not the bitmap.

### 4. Sharp flat card on paper page
Page `background: #F2EDE4`; card `background: #fff; border: 1px solid #E0DDD8; border-radius: 0; box-shadow: none; max-width: 600px` (600px is the email-safe convention vs. current 520px). Removes `box-shadow` (Outlook ignores it anyway) per landing flat-by-default rule. White card on paper page kept deliberately: pure paper-on-paper washes out in Gmail dark mode; white preserves contrast while page still reads warm.
- Alternative (paper card, no white): rejected for contrast reasons above.

### 5. Type: Georgia serif titles + crimson eyebrow, sans body
`h1`: `Georgia, 'Times New Roman', serif; color: #1A1A1A; 24-28px; lh 1.15`. Above it, eyebrow `10-11px uppercase 0.22em crimson` (landing Eyebrow Rule: every section opens with eyebrow + serif title — each mail is a section). Body sans `14-15px lh 1.7`, meta/muted `#8A8478`. Georgia is email-safe (Outlook, Apple Mail, Gmail all ship it), unlike landing webfonts that would need fallback anyway.

### 6. CTA: crimson block anchor, inline styles
`<a href="..." style="background:#C41E3A;color:#F2EDE4;padding:15px 32px;text-transform:uppercase;letter-spacing:0.1em;font-size:11px;text-decoration:none;display:inline-block;border:1px solid #C41E3A;">` — mirrors `Btn.astro:primary` but as a bulletproof anchor (no `<button>`, Outlook-safe). Used today only in `sale_reserved_buyer.html`; after migration any body can fill the `cta` block (checkout URL, delivery link). Inline styles duplicated on the anchor itself because some clients strip `<style>` — belt and suspenders.

### 7. Minimal footer
One bordered-top block: reply-hint line (`Si tienes alguna duda, responde a este correo…` — already in most bodies, deduplicated to footer) + `© {year} Enredarte · info@enredarte.com`. No socials, no legal links, no phone/WhatsApp (operator decision). Year passed from branding context.

### 8. Bilingual buyer bodies keep both sections
`sale_*_buyer.html` carry ES followed by EN with an `<hr>` divider. Migration keeps both, restyles divider to `#E0DDD8` and gives the EN section its own eyebrow + serif title (same shell blocks, second instance). No copy changes, no split into separate mails.

## Risks / Trade-offs

- [Risk] Outlook strips `<style>` and ignores `max-width`/`border-radius` nuances → Mitigation: all critical CTA/wordmark styling also inline; layout is single-column 600px table-free div (divs are fine in modern Outlook; no nested-table rebuild — accepted minor degradation in legacy Outlook).
- [Risk] Gmail/Apple dark-mode inverts paper `#F2EDE4` unpredictably → Mitigation: text wordmark + ink-on-white card degrades gracefully; no background-image or logo to break; accepted residual tint shift.
- [Risk] 36-file migration drifts TXT vs HTML → Mitigation: task per audience-group with explicit TXT-sync check; tests assert both alternatives exist (`email-notifications` Scenario "Every cash email has HTML and text bodies" pattern).
- [Risk] Template-override tests break (`render_to_string("artworks/email/sale_paid_buyer.html")` now pulls base) → Mitigation: base uses only guaranteed context keys with `|default`; `send_audience` injects brand/footer defaults so direct `render_to_string` in tests still resolves.
- [Risk] Scope creep into copy/subject changes → Mitigation: spec explicitly freezes subjects/bodies/audiences; review rejects any copy diff beyond wrapper moves.
- [Trade-off] Single shared base couples both domains to `core` templates — accepted: `core` already owns the renderer, and coupling is the point of centralization.
