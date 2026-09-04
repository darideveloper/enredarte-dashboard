## Why

Operators manage artists in `ArtistAdmin` but must jump to a separate `ArtistSubscription` changelist to inspect Stripe state (`status`, `stripe_customer_id`, `signup_url`, `raw_state`, etc.). This split hides commercial truth from the primary workflow and forces extra clicks for the most common support task ("is this artist paid? where is the link?"). Showing the subscription as a read-only inline inside the artist form puts all Stripe data where the operator already works, without allowing inline mutation of Stripe-owned state.

## What Changes

- Add a read-only `ArtistSubscriptionInline` (`unfold.admin.StackedInline`) to `ArtistAdmin` that renders **all** `ArtistSubscription` fields (minus the redundant `artist` FK) in a single Unfold card as an ordered flat field list (`fields` + `readonly_fields`, proven Unfold pattern) and fully `readonly`.
- Render `status` as a colored badge (same palette as `subscription_badge`), `signup_url` as a clickable link + copy button with expiry awareness (copy affordance only when non-expired; "(expirado)" hint when past or empty), and `raw_state` as a pretty-printed `<pre>` final trailing flat field titled "Auditoría" (ordered flat `fields`, no `fieldsets`/collapse — per 2026-09-03 decision).
- Enforce read-only inline semantics: `extra=0`, `max_num=1`, `min_num=0`, `can_delete=False`, `has_add_permission=False`, `has_delete_permission=False`, `show_change_link=True` to the standalone `ArtistSubscription` admin.
- Handle the empty state ("Sin suscripción — usa 'Generar link de suscripción' arriba.") when the artist has no subscription row (inline header remains but shows a muted message rather than a blank form).
- Keep the separate `ArtistSubscriptionAdmin` registered for search/filter/debug; wire the inline's "Ver suscripción completa" link to it.
- Update Django admin counts/annotation: ensure change form prefetch avoids N+1 and does not interfere with existing `get_queryset` annotations for `_has_subscription`/`_subscription_status`.

## Capabilities

### New Capabilities
- *None — no new domain concept; this is a presentation change.*

### Modified Capabilities
- `artist-admin`: Add `ArtistSubscription` read-only `StackedInline` to the `Artist` change form, with field grouping, badge/link/JSON rendering, empty-state message, and link to the full subscription admin. Existing inlines (`ArtistTranslation`, `ArtistSocialLink`) and action buttons (`generate_link`, `regenerate_link`, `open_portal`, `sync_from_stripe`) remain unchanged.

## Impact

- **Code:** `artworks/admin.py` (new `ArtistSubscriptionInline` class + `ArtistAdmin.inlines` entry) plus a small template override `templates/admin/subscriptions/artistsubscription/edit_inline/stacked.html` for the empty state; `subscriptions/admin_helpers.py` helpers reused for badge rendering. Definitive location is `artworks/admin.py` to avoid circular import (`artworks/admin.py` already imports `BillingPlan` from `subscriptions`).
- **Admin UI:** `Artist` change form gains one additional card titled "Suscripción" (singular, Spanish); no database migration; no API change.
- **Tests:** `artworks/tests.py` `ArtistAdminTestCase` inline assertions need updating; optional new tests for read-only inline rendering and empty state.
- **Dependencies:** None. Relies on existing `django-unfold==0.77.1` `StackedInline`/`BaseInlineMixin` support for `readonly_fields`/`show_change_link` and Django 5.2 inline semantics (`max_num=1` for `OneToOne`).
- **Risk:** Low — read-only inline cannot mutate Stripe state; `has_add/delete→False` prevents phantom creates. Performance impact is one extra query per change-form load (FK filter on `artistsubscription`).
