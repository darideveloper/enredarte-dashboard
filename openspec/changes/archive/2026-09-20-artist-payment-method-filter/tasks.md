## 1. Artist payment-method filter (top)

- [x] 1.1 Add `ArtistPaymentMethodFilter` in `artworks/admin.py` next to `ArtistAvailableWorksFilter` (title `Método de pago`, param `payment_method`, lookups `online`/`cash`/`none`, `Exists`/`OuterRef` queryset branches).
- [x] 1.2 Insert the filter as the **first** entry of `ArtistAdmin.list_filter`.
- [x] 1.3 Add `payment_method` to `ArtistSubscriptionAdmin.list_filter` in `subscriptions/admin.py`.

## 2. Badge enrichment (annotation-safe)

- [x] 2.1 Annotate `_payment_method` via `Subquery` in `ArtistAdmin.get_queryset` alongside `_subscription_status`.
- [x] 2.2 Prefix `subscription_badge_from_artist` label with `Efectivo ·` / `En línea ·`, keep status colors and muted `Sin suscripción`, fall back to status-only when the annotation is absent.

## 3. Tests

- [x] 3.1 Extend `test_artist_admin_filters` to assert the new filter is present and first.
- [x] 3.2 Add behavior tests for `online` / `cash` / `none` / unfiltered querysets (mirror `test_artist_available_works_filter`).
- [x] 3.3 Add badge tests for cash prefix, online prefix, and no-subscription muted text.
- [x] 3.4 Run `venv/bin/python manage.py test artworks subscriptions --verbosity=2` and the admin changelist query-count check; confirm no per-row subscription queries.
