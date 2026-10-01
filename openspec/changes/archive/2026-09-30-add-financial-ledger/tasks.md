## 1. Scaffold `finance` app

- [x] 1.1 Create the `finance` app (`apps.py` with `verbose_name = "Finanzas"`, `__init__.py`, `models.py`, `admin.py`, `migrations/`), register `"finance"` in `project/settings.py` `INSTALLED_APPS`, and add a "Finanzas" entry to the Unfold sidebar navigation.
- [x] 1.2 Define the `FinancialEntry` model per the `financial-ledger` spec: `Kind` and `Currency` `TextChoices` with Spanish display labels (English values), signed `amount`, `occurred_on`, `artist`/`order`/`subscription` nullable FKs, `payment_method` (`cash`/`stripe`, labels "Efectivo"/"En línea"), `reference`, `note`, `reconciled`, Spanish `verbose_name`/`help_text` on every field, and a content-based `__str__`.
- [x] 1.3 Add a `Meta.ordering` (e.g. `-occurred_on`, `-id`) and a **partial** unique constraint on (`kind`, `reference`) applied only when `reference != ""`; ensure refund reversals use a distinct reference (original key + `-refund`) so they do not collide with the original sale/commission rows.
- [x] 1.4 Generate and apply the schema migration via `venv/bin/python manage.py makemigrations finance` / `migrate`.

## 2. Ledger service

- [x] 2.1 Create `finance/services.py` with helpers to build/insert entries: `record_artwork_sale(order)`, `record_artwork_refund(order)`, `record_subscription_payment(...)`.
- [x] 2.2 Implement commission snapshot inside `record_artwork_sale` (percentage from `artist.commission`, skip when `0`, negative `amount`).
- [x] 2.3 Implement reversal logic in `record_artwork_refund` (negate original sale, reverse commission) without mutating original rows.
- [x] 2.4 Enforce idempotency via `reference` (invoice id / payment intent id / cash period key) so repeated calls do not double-book.

## 3. Write hooks

- [x] 3.1 Call `record_artwork_sale` from `artworks/services.py:apply_paid_transition` (same transaction as the paid transition).
- [x] 3.2 Call `record_artwork_refund` from the refund paths (`artworks/order_webhooks.py:_apply_artwork_paid` and `artworks/services.py:_apply_reconciled_paid`).
- [x] 3.3 Call `record_subscription_payment` from `subscriptions/webhooks.py:_handle_invoice_payment_succeeded` using invoice `amount_paid`/`currency`/id.
- [x] 3.4 Call `record_subscription_payment` from the cash "Confirmar pago" action in `artworks/admin.py`, snapshotting `BillingPlan.amount`/`currency` and keying by the resulting period.
- [x] 3.5 Verify no ledger write occurs for cash rows in the Stripe handler and for unpaid/cancelled orders.

## 4. Backfill migration

- [x] 4.1 Add a data migration creating `artwork_sale` (+ `artist_commission`) entries for `ArtworkOrder` rows with `paid_at` and a paid (non-refunded/cancelled) status, using each artist's current commission.
- [x] 4.2 Make the migration idempotent and reversible (delete backfill-referenced rows on reverse); document that pre-existing subscription payments are not backfilled.

## 5. `Finanzas` admin

- [x] 5.1 Register `FinancialEntryAdmin` (Unfold) with `list_display` (date, kind, artist, signed color-coded amount, currency, reference, `reconciled`), `list_editable = ["reconciled"]`, all other fields readonly, and `has_add_permission`/`has_delete_permission` returning `False`.
- [x] 5.2 Add `date_hierarchy = "occurred_on"` and `list_filter` for date range, `artist`, `kind`, `payment_method`, `currency`, and `reconciled`.
- [x] 5.3 Override `changelist_view` to compute, per currency, income (`Sum` over positive amounts), expenses (`Sum` over negative amounts), net, and count — over **both** `cl.queryset` (filtered → "Vista actual") and `cl.root_queryset` (all-time → "Total del sistema"), guarding for responses without `context_data` (POST redirect / action form).
- [x] 5.4 Add a small totals partial rendered via Unfold's native `list_after_template` (not a `change_list.html` override), showing income / expense / net per currency for both filtered and full-system totals, with Spanish labels ("Vista actual", "Total del sistema", "Ingresos", "Comisiones", "Neto").
- [x] 5.5 Confirm no ledger/admin code is exposed via any public API or serializer.
- [x] 5.6 Ensure every admin-visible text is Spanish per `docs/django-i18n-es-admin.md`: app `verbose_name`, model name, field labels/help_text, choice labels, column headers, filter titles, totals partial labels, and empty-state text (Django's shipped `es` catalog handles generic chrome via `LANGUAGE_CODE = "es"`).

## 6. Tests (Django `manage.py test`)

- [x] 6.1 Model tests: signed convention, defaults, `__str__`, Spanish metadata, ordering.
- [x] 6.2 Sale hook tests: two entries with frozen commission, zero-commission case, idempotent paid transition.
- [x] 6.3 Refund tests: reversal nets to zero, idempotency, no original mutation.
- [x] 6.4 Subscription tests: Stripe invoice snapshots actual amount/currency and dedupes by reference; cash confirm snapshots plan amount; plan price change does not alter past entries; cash rows ignored by Stripe.
- [x] 6.5 Backfill tests: paid orders get entries, unpaid/cancelled skipped, migration idempotent.
- [x] 6.6 Admin tests: `reconciled` inline edit persists, add/delete blocked, filters and date drill-down return filtered sets, the filtered total reflects the active filters (income / expense / net), the full-system total ignores filters and shows all-time (even with zero results), both totals are split per currency, and income − expenses equals the net per line.
- [x] 6.7 Spanish-label tests: model `verbose_name`/`help_text`, choice display labels, and the changelist totals labels render in Spanish (assert "En línea", "Efectivo", "Vista actual", "Total del sistema").

## 7. Verification

- [x] 7.1 Run the full targeted suite: `venv/bin/python manage.py test finance subscriptions artworks --verbosity=2` (adjust labels as needed).
- [x] 7.2 Run the project test-contract guard (`/.opencode/commands/guard.sh`) and confirm no pytest artifacts were introduced.
- [x] 7.3 Manually verify in the Unfold admin: month drill-down, each filter, totals per currency, and inline `reconciled` toggle.
