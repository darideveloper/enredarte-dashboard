## 1. Buyer template copy

- [x] 1.1 Add price note + certificate line, universal variant (`Todas nuestras obras incluyen…` / `All our artworks include…`), ES + EN, plain `<p>` in HTML, to `sale_reserved_buyer.txt` and `sale_reserved_buyer.html`
- [x] 1.2 Add price note + certificate line, direct variant (`Tu obra incluye…` / `Your artwork includes…`), ES + EN, plain `<p>` in HTML, to `sale_paid_buyer.txt` and `sale_paid_buyer.html`
- [x] 1.3 Add price note only (ES + EN, plain `<p>` in HTML) to `sale_refunded_buyer.txt` and `sale_refunded_buyer.html`

## 2. Verification

- [x] 2.1 Grep all 6 files for the new ES + EN sentences (both alternatives present, no drift)
- [x] 2.2 Render-check one buyer mail per kind (reserved / paid / refunded) via Django template render with a fake order context
- [x] 2.3 Run `venv/bin/python manage.py test artworks --verbosity=2` (sale mail suites: `SaleEmailNotificationsTest`, `ArtworkOrderWebhookEmailTest`) and confirm green
