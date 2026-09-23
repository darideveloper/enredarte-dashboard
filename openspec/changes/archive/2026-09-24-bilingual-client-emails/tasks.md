## 1. Checkout and Purchase Templates

- [x] 1.1 Update `sale_reserved_buyer.html` and `sale_reserved_buyer.txt` with English translation and divider; verify both HTML and TXT contain the checkout URL and 30-minute hold notice in both languages.
- [x] 1.2 Update `sale_paid_buyer.html` and `sale_paid_buyer.txt` with English translation and divider; verify artwork title, amount, currency, and delivery instructions render in both languages.
- [x] 1.3 Update `sale_delivery_complete_buyer.html` and `sale_delivery_complete_buyer.txt` with English translation and divider; verify shipment preparation notice renders in both languages.

## 2. Fulfillment Templates

- [x] 2.1 Update `sale_shipped_buyer.html` and `sale_shipped_buyer.txt` with English translation and divider; verify shipping notification renders in both languages.
- [x] 2.2 Update `sale_delivered_buyer.html` and `sale_delivered_buyer.txt` with English translation and divider; verify delivery confirmation and thank-you text render in both languages.

## 3. Exception Templates

- [x] 3.1 Update `sale_cancelled_buyer.html` and `sale_cancelled_buyer.txt` with English translation and divider; verify cancellation notice and availability guidance render in both languages.
- [x] 3.2 Update `sale_refunded_buyer.html` and `sale_refunded_buyer.txt` with English translation and divider; verify refund notification and bank timing note render in both languages.

## 4. Subject Lines and HTML Titles

- [x] 4.1 Update `_SALE_SUBJECTS` for buyer entries in `subscriptions/services/notifications.py` to use bilingual format (`Spanish / English`).
- [x] 4.2 Update `<title>` tag in all 7 buyer HTML templates to reflect the bilingual subjects.

## 5. Testing and Verification

- [x] 5.1 Update unit tests in `artworks/tests.py` and `subscriptions/tests.py` to assert the new bilingual subject strings.
- [x] 5.2 Run Django test suite (`venv/bin/python manage.py test artworks.tests.SaleEmailNotificationsTest subscriptions.tests.ArtworkOrderWebhookEmailTest`) and verify all tests pass.
- [x] 5.3 Verify manual rendering and mail dispatch in local environment to ensure subject lines and bodies appear as expected in Mailpit.
