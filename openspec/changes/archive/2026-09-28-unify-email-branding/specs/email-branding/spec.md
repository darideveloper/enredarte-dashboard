## ADDED Requirements

### Requirement: Centralized email brand shell
The system SHALL provide one shared HTML shell `project/templates/email/base.html` (with header/footer includes) that all 36 transactional HTML templates extend, so no per-mail template carries its own `<head>`, `<style>`, page, or card styling.

#### Scenario: Sale mail extends the shared shell
- **WHEN** `artworks/email/sale_paid_buyer.html` is rendered
- **THEN** it SHALL `{% extends "email/base.html" %}` and SHALL NOT contain its own `<style>` block or `#1d3a2f` / `#faf7f2` literals.

#### Scenario: Subscription mail extends the shared shell
- **WHEN** `subscriptions/email/cash_active.html` is rendered
- **THEN** it SHALL `{% extends "email/base.html" %}` and SHALL NOT contain its own `<style>` block or `#1d3a2f` / `#faf7f2` literals.

### Requirement: Landing token source for mail
The system SHALL provide `core/mail_branding.py` exposing the landing palette/typography as one importable source (`paper #F2EDE4`, `ink #1A1A1A`, `crimson #C41E3A`, `muted #8A8478`, `border #E0DDD8`, `banner #EAE4D8`, Georgia serif display + system sans body), and `core/mail_utils.py:send_audience` SHALL inject these tokens plus footer contact into every render context, so templates reference `{{ brand.* }}` and never hardcode brand hex.

#### Scenario: Tokens resolve in every mail
- **WHEN** any sale or subscription sender renders its HTML body
- **THEN** the context SHALL contain `brand` with `paper`, `ink`, `crimson`, `muted`, and `border` keys matching the landing values above.

#### Scenario: Base renders without injected context
- **WHEN** a template extending the base is rendered directly via `render_to_string` without sender context (as existing tests do)
- **THEN** the output SHALL still render with fallback brand/footer values and SHALL NOT raise.

### Requirement: Landing visual contract for mail bodies
Every transactional HTML mail SHALL render: paper page background, white sharp card (`border-radius: 0`, 1px `#E0DDD8` border, no shadow, ≤600px centered), Georgia serif title in ink with a crimson uppercase tracked eyebrow above it, sans body (`14-15px`), muted meta in `#8A8478`, and `#E0DDD8` dividers — with no forest-green `#1d3a2f`, no rounded cards, and no resting shadows.

#### Scenario: New shell matches landing geometry
- **WHEN** any migrated HTML mail is rendered
- **THEN** the output SHALL contain `border-radius: 0`, `Georgia`, `#C41E3A`, `#F2EDE4`, and `#E0DDD8`, and SHALL NOT contain `#1d3a2f` or `border-radius: 16px`.

### Requirement: Text wordmark header
Every HTML mail SHALL open with a text wordmark header (`ENREDARTE`, Georgia serif, uppercase, tracked, ink) with a short crimson rule, and SHALL contain no `<img>`, logo file reference, or external image URL.

#### Scenario: Header has no image dependency
- **WHEN** any migrated HTML mail is rendered
- **THEN** the output SHALL contain `ENREDARTE` as text and SHALL NOT contain `<img`, `logo.png`, or `favicon`.

### Requirement: Crimson block CTA
Any mail with an action link (today: reserved checkout URL; future: delivery links) SHALL render it as a crimson block anchor (crimson background, paper text, sharp corners, uppercase tracked label, inline styles on the anchor), mirroring the landing primary button.

#### Scenario: Reserved buyer CTA is crimson block
- **WHEN** `sale_reserved_buyer.html` is rendered with a `checkout_url`
- **THEN** the checkout anchor SHALL carry inline `background:#C41E3A` styling with uppercase tracked text and sharp corners.

### Requirement: Minimal text footer
Every HTML mail SHALL close with a minimal footer block: reply-hint line plus `© {year} Enredarte · info@enredarte.com`, separated by a `#E0DDD8` rule; no social icons, legal links, phone, or WhatsApp entries.

#### Scenario: Footer carries contact without socials
- **WHEN** any migrated HTML mail is rendered
- **THEN** the output SHALL contain `info@enredarte.com` and `©`, and SHALL NOT contain `facebook.com`, `instagram.com`, or `wa.me`.

### Requirement: Bilingual bodies preserved inside the shell
Buyer mails that today carry Spanish + English in one template (`sale_reserved_buyer`, `sale_paid_buyer`, `sale_delivery_complete_buyer`, `sale_shipped_buyer`, `sale_delivered_buyer`, `sale_cancelled_buyer`, `sale_refunded_buyer`) SHALL keep both language sections with the same copy, restyled with the shared divider and a repeated eyebrow + serif title for the English section.

#### Scenario: Paid buyer keeps both languages
- **WHEN** `sale_paid_buyer.html` is rendered
- **THEN** the output SHALL contain both `Tu pago fue confirmado` and `Payment confirmed` with the same amounts/instructions as today.

### Requirement: Behavior freeze around the re-brand
Audiences, subjects, firing/transition-gating rules, best-effort and `transaction.on_commit` semantics, and TXT+HTML pairing for all existing senders SHALL remain exactly as specified in `email-notifications`, `sales-emails`, and `subscription-emails`; this capability changes only the HTML shell/styling, never who is mailed, when, or with what subject.

#### Scenario: Paid trio still mails three audiences
- **WHEN** `send_sale_paid(order)` runs with buyer, artist, and admin addresses configured
- **THEN** three TXT+HTML messages SHALL still be sent with today's subjects, only the HTML shell styling having changed.

#### Scenario: Every migrated mail keeps both alternatives
- **WHEN** any migrated sender runs
- **THEN** each message SHALL still contain both `text/plain` and `text/html` alternatives rendering the same information.
