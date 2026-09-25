## Context

Currently, all client-facing transactional emails for artwork sales are written exclusively in Spanish across 14 template files (7 `.html` + 7 `.txt`) in `subscriptions/templates/subscriptions/email/`. The user requested keeping the exact same email subjects in Spanish while providing an English version of the text directly within the same template body.

See `proposal.md` for motivation and `specs/sales-emails/spec.md` for requirements.

## Goals / Non-Goals

**Goals:**
- Provide complete English translations in both HTML and plain text formats for all 7 buyer notification events:
  1. `sale_reserved_buyer`
  2. `sale_paid_buyer`
  3. `sale_delivery_complete_buyer`
  4. `sale_shipped_buyer`
  5. `sale_delivered_buyer`
  6. `sale_cancelled_buyer`
  7. `sale_refunded_buyer`
- Retain exact Spanish content in the top section and present the English version in the bottom section separated by a subtle visual divider.
- Keep all email subjects unchanged in Spanish in `subscriptions/services/notifications.py`.
- Ensure all automated tests (`artworks/tests.py`) continue to pass without regression.

**Non-Goals:**
- No multi-locale routing or user language preferences (e.g. separate `en` vs `es` email dispatch).
- No modifications to artist notices or admin operational notifications.
- No modifications to cash subscription or online subscription templates.

## Decisions

### Decision 1: Stacked bilingual layout (Spanish primary on top, English secondary below)
- **Choice**: Display the Spanish notification first, followed by a divider and the English equivalent.
- **Rationale**: Preserves the primary platform language and identity while immediately assisting international buyers without requiring additional preference settings or backend state.
- **Alternatives considered**:
  - *Side-by-side columns*: Poor responsive behavior on mobile email clients.
  - *Dynamic language selection based on browser/header*: The API order flow currently does not capture buyer preferred locale, and storing extra language state adds unnecessary backend complexity.

### Decision 2: Consistent divider styling across formats
- **HTML**:
  ```html
  <hr style="border: 0; border-top: 1px solid #e5e0d8; margin: 24px 0;">
  ```
  Followed by an `<h2>` styled similarly to `<h1>` but sized appropriately (`font-size: 18px; color: #1d3a2f`).
- **Plain Text**:
  ```text
  --------------------------------------------------
  (English version below)
  ```
  Ensures clear visual demarcation in text-only mail clients.

### Decision 3: Shared context variable interpolation
- Both Spanish and English copy interpolate the same context keys (`artwork_title`, `currency`, `amount`, `checkout_url`).
- In `sale_reserved_buyer.html`, both Spanish and English call-to-action buttons link to `{{ checkout_url }}`.

### Decision 4: Bilingual email subjects with slash separator
- **Choice**: `Spanish / English` format (e.g. `Tu pago fue confirmado / Payment confirmed`).
- **Rationale**: Immediate clarity in inbox previews before opening the message, maintaining concise lengths (<60 characters) to prevent mobile truncation.
- **Scope**: Modifies `_SALE_SUBJECTS` for buyer entries in `subscriptions/services/notifications.py` and `<title>` tags in HTML templates.

## Risks / Trade-offs

- **[Risk] Email length and clipping in email clients (e.g. Gmail 102KB clipping)**:
  → *Mitigation*: The email bodies are concise (150–250 words total across both languages) and total HTML size is well under 3KB per template, far below any client clipping limits.
- **[Risk] Regression in existing tests asserting email subjects**:
  → *Mitigation*: Update assertions in `artworks/tests.py` and `subscriptions/tests.py` to match the exact new bilingual subject strings.

## Open Questions

None. The requirements, scope, and translations are fully defined.
