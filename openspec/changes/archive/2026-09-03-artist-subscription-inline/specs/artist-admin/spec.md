## ADDED Requirements

### Requirement: ArtistSubscription read-only inline on Artist admin

The system SHALL display the related `ArtistSubscription` as a read-only `StackedInline` inside the `Artist` change form in Django Unfold, showing **all** `ArtistSubscription` displayable fields (minus the redundant `artist` FK) as an ordered flat field list and fully non-editable, with a link to the standalone subscription admin.

#### Scenario: Viewing subscription data inline when artist has a subscription
- **WHEN** an administrator opens the change form for an `Artist` that has a related `ArtistSubscription`
- **THEN** a card titled "Suscripción" (singular, Spanish) SHALL be rendered below the existing translation and social-link inlines, showing in read-only form: the colored status badge (same palette as `subscription_badge`), `stripe_customer_id`, `stripe_subscription_id`, `customer_email`, `current_period_end`, `cancel_at_period_end`, `signup_url` as a clickable link, `signup_url_expires_at`, `last_synced_at`, `created_at`/`updated_at`, and `raw_state` pretty-printed as the final trailing field, ordered flat (no `fieldsets`) and never as editable inputs.

#### Scenario: Clickable signup_url with expiry awareness
- **WHEN** the inline renders `signup_url` and `signup_url_expires_at`
- **THEN** the URL SHALL be displayed as a clickable `<a href="...">` (target `_blank`) and, when non-expired, SHALL expose the same copy affordance as the change-view header (`data-copy-url`), with a visual hint "(expirado)" when `signup_url_expires_at` is in the past or empty; the raw URL text SHALL still be visible for audit.

#### Scenario: Raw Stripe state is human-readable
- **WHEN** the inline renders `raw_state` (JSONField)
- **THEN** the content SHALL be rendered as pretty-printed JSON (`json.dumps(..., indent=2, ensure_ascii=False)`) inside a scrollable `<pre>` block as the final trailing flat field titled "Auditoría" (no `fieldsets`/collapse), plus reachable via the `show_change_link` standalone detail, not as a raw Python `str(dict)` or truncated text.

#### Scenario: Empty state when artist has no subscription
- **WHEN** an administrator opens the change form for an `Artist` that has no related `ArtistSubscription`
- **THEN** the inline card header SHALL remain visible and SHALL render a muted message "Sin suscripción — usa 'Generar link de suscripción' arriba." rather than a blank editable form or no affordance at all.

#### Scenario: Inline is strictly read-only and non-creatable
- **WHEN** any POST is submitted against the `Artist` change form containing the `ArtistSubscription` inline formset
- **THEN** no new `ArtistSubscription` row SHALL be created, no existing row SHALL be mutated, and no row SHALL be deleted via the inline; the inline formset SHALL have `extra=0`, `max_num=1`, `min_num=0`, `can_delete=False`, `has_add_permission=False`, and `has_delete_permission=False`, and every field SHALL be in `readonly_fields`.

#### Scenario: Inline links to full subscription admin and coexists with action buttons
- **WHEN** the inline is rendered
- **THEN** a "Ver suscripción completa" change link (`show_change_link=True`) SHALL be present that navigates to the standalone `ArtistSubscription` change page, and the inline SHALL coexist with the existing `ArtistAdmin` action buttons ("Generar / Regenerar link", "Abrir Customer Portal", "Sincronizar desde Stripe") without positional or permission conflict; the separate `ArtistSubscriptionAdmin` SHALL remain registered for search/filter by `artist__name`, `artist__email`, `stripe_*_id` and filters on `status` / `artist_is_active`.

#### Scenario: No regression on existing artist admin inlines and counts
- **WHEN** the subscription inline is added
- **THEN** existing inlines (`ArtistTranslationInline`, `ArtistSocialLinkInline`) and readonly "Resumen" counts SHALL continue to render correctly, and existing changelist annotations (`_has_subscription`, `_subscription_status`, counts at `artworks/admin.py:322`) SHALL not be affected.
