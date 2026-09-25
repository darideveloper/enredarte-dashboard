## Why

Art buyers on the platform can be international and may not speak Spanish. Currently, all transactional client-facing emails (artwork reservations, purchase confirmations, shipping, delivery, cancellations, and refunds) are sent exclusively in Spanish. Providing an English translation alongside the existing Spanish text in the same email ensures clarity and accessibility for English-speaking clients while preserving the existing Spanish content and operational conventions.

## What Changes

- Update all 7 client-facing (buyer) email templates in `subscriptions/templates/subscriptions/email/` to include a complete English translation alongside the original Spanish text:
  - `sale_reserved_buyer.html` and `sale_reserved_buyer.txt`
  - `sale_paid_buyer.html` and `sale_paid_buyer.txt`
  - `sale_delivery_complete_buyer.html` and `sale_delivery_complete_buyer.txt`
  - `sale_shipped_buyer.html` and `sale_shipped_buyer.txt`
  - `sale_delivered_buyer.html` and `sale_delivered_buyer.txt`
  - `sale_cancelled_buyer.html` and `sale_cancelled_buyer.txt`
  - `sale_refunded_buyer.html` and `sale_refunded_buyer.txt`
- Maintain Spanish content first, followed by a clean visual divider and the English equivalent.
- Update email subject lines for all 7 buyer notifications in `subscriptions/services/notifications.py` (`_SALE_SUBJECTS`) to be bilingual using the `Spanish / English` format.
- Retain all template variables (`{{ artwork_title }}`, `{{ currency }}`, `{{ amount }}`, `{{ checkout_url }}`) in both sections.

## Capabilities

### New Capabilities

### Modified Capabilities
- `sales-emails`: Update the 7 buyer email templates to be bilingual (Spanish + English in the same template body for both HTML and TXT formats) and update the 7 buyer email subjects to bilingual format (`Spanish / English`).

## Impact

- **Templates**: Updates 14 template files (7 `.html` + 7 `.txt`) in `subscriptions/templates/subscriptions/email/` and their `<title>` tags.
- **Subject lines & Senders**: Updates `_SALE_SUBJECTS` in `subscriptions/services/notifications.py` for buyer notifications.
- **Backend/API/Models**: Zero schema or endpoint changes.
- **Tests**: Updates test assertions in `artworks/tests.py` and `subscriptions/tests.py` to match the bilingual subject format.
