## Why

Buyers see `Monto: {{ currency }} {{ amount }}` in reservation/payment/refund mails, but `ArtworkOrder.amount` is the artwork price only — delivery cost is agreed separately and has no model field. Without a note, buyers can assume delivery is included. At the same time the sale never tells the buyer that every work ships with a certificate of authenticity and team-coordinated secure delivery, which is a trust gap at the two money moments (reserved, paid).

## What Changes

- Add a static vague price-clarification note (ES + EN) to the three buyer templates that render an amount: `sale_reserved_buyer`, `sale_paid_buyer`, `sale_refunded_buyer` (both `.txt` and `.html`).
- Add a static certificate + secure-delivery reassurance line (ES + EN) to the two money-moment buyer templates: `sale_reserved_buyer`, `sale_paid_buyer` (both `.txt` and `.html`).
- No subject changes, no audience changes, no sender/code changes, no model or Stripe changes. Pure template copy change, best-effort semantics unchanged.
- Copy follows the existing inline dual-language pattern (Spanish first, English section after), no `locale/` or `{% trans %}` migration.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `sales-emails`: buyer body requirements for reserved / paid / refunded gain the price-excludes-delivery note; reserved / paid buyer bodies gain the certificate + secure-delivery line. Subjects, audiences, triggers, and best-effort guarantees are unchanged.

## Impact

- Affected files: 6 template files under `artworks/templates/artworks/email/` (`sale_reserved_buyer.txt/.html`, `sale_paid_buyer.txt/.html`, `sale_refunded_buyer.txt/.html`). Each edited twice (ES block + EN block).
- No Python changes (`artworks/sale_notifications.py`, `core/mail_utils.py` untouched); no migrations; no Stripe/API changes.
- Risk: negligible — static copy only. Existing tests (`SaleEmailNotificationsTest`, `ArtworkOrderWebhookEmailTest`) assert subjects/audiences, not the new sentences, so they keep passing.
