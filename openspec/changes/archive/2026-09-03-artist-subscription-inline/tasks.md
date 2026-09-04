## 1. Inline definition — read-only StackedInline

- [x] 1.1 Create `ArtistSubscriptionInline` as `unfold.admin.StackedInline` (`fk_name="artist"`, `verbose_name="Suscripción"`, `verbose_name_plural="Suscripción"`, `extra=0`, `max_num=1`, `min_num=0`, `can_delete=False`, `show_change_link=True`) definitively in `artworks/admin.py`, importing `ArtistSubscription` and `subscription_badge` from `subscriptions/admin_helpers.py`.
- [x] 1.2 Define `fields`/`readonly_fields` as the 12 displayable `ArtistSubscription` fields (minus `artist`) plus 3 custom methods: `display_status`, `display_signup_url`, `display_raw_state`; set `readonly_fields = fields` so every rendered field is non-editable.
- [x] 1.3 Implement `display_status` (`@admin.display(description="Estado")`) returning `subscription_badge(obj)` (handles `None`), `display_signup_url` (`@admin.display(description="Link de pago")`) returning `format_html` clickable link + `data-copy-url` (only when `_link_is_valid`: `signup_url` present and `signup_url_expires_at` not past) + "(expirado)" hint when past or empty, and `display_raw_state` (`@admin.display(description="Auditoría")`) returning `json.dumps(obj.raw_state, indent=2, ensure_ascii=False)` in a scrollable `<pre>`; guard each method against `obj is None`.
- [x] 1.4 Enforce read-only permissions on the inline: `has_add_permission` → `False`, `has_delete_permission` → `False` (keep `has_change` truthy so the inline remains visible; rely on `readonly_fields` to block mutation).

## 2. ArtistAdmin wiring + field grouping

- [x] 2.1 Add `ArtistSubscriptionInline` to `ArtistAdmin.inlines` (`artworks/admin.py:228`) after `ArtistSocialLinkInline` (order: translations → social links → subscription) without altering existing `fieldsets`/`readonly_fields` for the "Resumen" section.
- [x] 2.2 Order inline fields flat (no `fieldsets`): `display_status`, `stripe_customer_id`, `stripe_subscription_id`, `customer_email`, `current_period_end`, `cancel_at_period_end`, `display_signup_url`, `signup_url_expires_at`, `last_synced_at`, `created_at`, `updated_at`, `display_raw_state` (trailing). Flat ordering is the proven pattern in this repo; do not introduce `fieldsets`.

- [x] 2.3 Verify `ArtistAdmin.get_queryset` annotations (`_has_subscription`/`_subscription_status` at `artworks/admin.py:322`) and `change_view` `copy_button_extra_attrs` (`:270`) are unaffected; optionally add `select_related("subscription")` for the change form queryset.

## 3. Empty-state handling

- [x] 3.1 Add inline template `templates/admin/subscriptions/artistsubscription/edit_inline/stacked.html` extending Unfold's stacked inline that renders the muted message "Sin suscripción — usa 'Generar link de suscripción' arriba." when `inline_admin_formset.formset.queryset|length == 0` and `extra == 0`; set `ArtistSubscriptionInline.template` to it.
- [x] 3.2 Verify empty state manually: open change form for an artist without a subscription row — header remains visible with the muted message, no blank form, no add button.

## 4. Visual verification + Unfold integration

- [x] 4.1 Manually verify in Unfold admin: artist with active subscription shows colored badge, clickable `signup_url`, copy affordance (only when valid), and scrollable pretty JSON as final flat field titled "Auditoría"; artist without subscription shows empty message; `show_change_link` navigates to standalone `ArtistSubscription` admin (`subscriptions/admin.py:181`) and that admin remains searchable/filterable.
- [x] 4.2 Verify no extra migration, no N+1, no console errors, and no positional regression on existing inlines or `display_*_detail` readonly fields (`artworks/admin.py:300`).

## 5. Tests

- [x] 5.1 Update `artworks/tests.py:ArtistAdminTestCase.test_artist_admin_has_translation_inline` and related inline assertions to include `ArtistSubscriptionInline` membership (assert set, not positional).
- [x] 5.2 Add tests: read-only inline renders status badge and signup_url link for an artist with subscription; empty-state muted message for an artist without subscription; `has_add_permission`/`has_delete_permission` return `False`; `max_num==1`/`can_delete==False` invariant.
- [x] 5.3 Run `python manage.py test artworks subscriptions` and confirm green (including existing `subscriptions/tests.py:ArtistAdminBadgeTest`).
