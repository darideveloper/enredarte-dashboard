## Purpose
Defines how the `Artist` model is registered in the Django Unfold admin and
how the change form is extended with subscription controls (commercial gate)
and translation inlines (Spanish/English bio). The Suscripción badge column
and the action buttons on the change form let operators manage paid
memberships from the same page that already manages the artist's bio.
## Requirements
### Requirement: Artist model admin registration
The system SHALL register the `Artist` model in `artworks/admin.py` using `ModelAdminUnfoldBase` so that artists are manageable within the Django Unfold admin site.

#### Scenario: Viewing artist list in admin
- **WHEN** an administrator opens the Django Admin panel
- **THEN** the sidebar SHALL display "Artistas" with a palette icon and list artists with columns for Name, Email, Birth Year, Death Year, Active state, and a "Suscripción" badge column showing the `ArtistSubscription.status` in Spanish (or "Sin suscripción" when the artist has no subscription row).

#### Scenario: Email is a required field for an active artist to obtain a payment link
- **WHEN** an administrator creates a new `Artist` (or edits an existing one) through the Django Unfold admin form
- **THEN** the `email` field MUST be required (`blank=False`, `null=False`) so the subscription payment-link flow can identify a Stripe customer.

### Requirement: Inline translation management for Artist
The system SHALL display `ArtistTranslation` as a `StackedInline` inside the `Artist` edit form in Django Admin to allow editing Spanish (`es`) and English (`en`) bio text on the same page, pre-populating Spanish (`es`) on the first form and English (`en`) on the second form during creation, and suppressing extra blank forms when all translations already exist.

#### Scenario: Editing artist translations
- **WHEN** an administrator accesses an Artist change page in the admin
- **THEN** an inline section titled "Traducciones" SHALL render existing translations without appending extra blank forms when Spanish and English translations are present.

#### Scenario: Creating a new artist with pre-populated translation languages
- **WHEN** an administrator accesses the new Artist creation page in the admin
- **THEN** the two translation inline forms SHALL render with default language selections set to Spanish (`es`) and English (`en`).

### Requirement: Artist admin form field ordering
The system SHALL organize the `ArtistAdmin` form using `fieldsets` to logically group fields and ensure `slug` directly follows `name`.

#### Scenario: Creating or editing an artist
- **WHEN** an administrator views the Artist add or edit form
- **THEN** fields SHALL be organized into logical sections (e.g., Personal Info, Contact & Media, System Status) with the `slug` field positioned immediately after `name` to visually support auto-population.

### Requirement: Location selector on Artist admin
The system SHALL add the `location` field to the `ArtistAdmin` edit form so an administrator can assign a shared `Location` to an artist.

#### Scenario: Assigning an artist location
- **WHEN** an administrator opens an Artist edit form
- **THEN** they can pick one `Location` for the artist (or leave it empty).

### Requirement: Social links inline on Artist admin
The system SHALL include the `ArtistSocialLinkInline` (`TabularInline`) in the `ArtistAdmin` edit form.

#### Scenario: Editing social links with the artist
- **WHEN** an administrator opens an Artist edit form
- **THEN** they can add and remove the artist's social links in place.

### Requirement: Changelist summary columns on Artist admin
The system SHALL add readonly count columns to the `ArtistAdmin` changelist for the derived blocks (artworks, available works, techniques, highlighted works, galleries), computed from the `Artist` derived properties (see `artist-derived-fields`).

#### Scenario: Viewing artist counts
- **WHEN** an administrator opens the Artist changelist
- **THEN** each row shows the computed counts for the derived blocks.

### Requirement: Readonly Resumen fieldset on Artist admin
The system SHALL render the derived profile blocks on the `ArtistAdmin` change form as a readonly "Resumen" fieldset in full detail, computed from the `Artist` derived properties (see `artist-derived-fields`).

#### Scenario: Viewing computed profile blocks
- **WHEN** an administrator opens an Artist edit form
- **THEN** the "Resumen" section displays the computed techniques, available works count, new additions, highlighted works, most viewed, and exhibiting galleries.

### Requirement: Artist location filter
The system SHALL add a `location` filter to the `ArtistAdmin` changelist so an administrator can browse artists by their assigned `Location`.

#### Scenario: Filtering artists by location
- **WHEN** an administrator opens the Artist changelist and selects a location in the "Ubicación" filter
- **THEN** only artists assigned to that location SHALL be shown.

#### Scenario: Location filter shows only in-use locations
- **WHEN** an administrator opens the Artist changelist and expands the "Ubicación" filter
- **THEN** only locations assigned to at least one artist SHALL be listed.

### Requirement: Artist created_at date filter
The system SHALL add `created_at` to the `ArtistAdmin` list filters so an administrator can filter artists by creation date range.

#### Scenario: Filtering recently onboarded artists
- **WHEN** an administrator opens the Artist changelist and applies a `created_at` date range
- **THEN** only artists created within that range SHALL be shown.

### Requirement: Artist has-artworks filter
The system SHALL add a "with/without artworks" filter to the `ArtistAdmin` changelist so an administrator can find artists with incomplete profiles (no artworks).

#### Scenario: Finding artists without artworks
- **WHEN** an administrator opens the Artist changelist and selects the "sin obras" lookup
- **THEN** only artists with no artworks SHALL be shown.

#### Scenario: Finding artists with artworks
- **WHEN** an administrator opens the Artist changelist and selects the "con obras" lookup
- **THEN** only artists with at least one artwork SHALL be shown.

### Requirement: Artist with-available-works filter
The system SHALL add a filter to the `ArtistAdmin` changelist that isolates artists currently having at least one active artwork with status `available`.

#### Scenario: Finding artists with sellable works
- **WHEN** an administrator opens the Artist changelist and selects the "con obras disponibles" lookup
- **THEN** only artists having at least one active `available` artwork SHALL be shown.

### Requirement: Artist changelist pagination
The system SHALL paginate the `ArtistAdmin` changelist at 50 rows per page.

#### Scenario: Browsing the Artist changelist
- **WHEN** an administrator opens the Artist changelist
- **THEN** at most 50 artists SHALL be rendered per page.

### Requirement: Subscription action buttons on Artist edit view
The system SHALL render three admin actions on the `ArtistAdmin` change view (next to the existing fieldset buttons), available only to staff: "Generar / Regenerar link de suscripción", "Abrir Customer Portal", and "Sincronizar desde Stripe". The buttons SHALL be wired to the corresponding endpoints declared in `specs/subscription-admin-controls/spec.md`.

#### Scenario: "Generar / Regenerar link" button is present
- **WHEN** an administrator opens an `Artist` change page
- **THEN** a button labelled "Generar link de suscripción" (or "Regenerar link" when an existing subscription's signup URL has expired) SHALL appear in the actions bar.

#### Scenario: "Abrir Customer Portal" button visible when relevant
- **WHEN** an administrator opens an `Artist` change page for an artist whose `ArtistSubscription.stripe_customer_id` is non-empty
- **THEN** a button labelled "Abrir Customer Portal" SHALL appear; clicking it SHALL trigger the endpoint from `specs/subscription-admin-controls/spec.md` and reveal the portal URL inline.

#### Scenario: "Sincronizar desde Stripe" button always available
- **WHEN** an administrator opens an `Artist` change page
- **THEN** a "Sincronizar desde Stripe" button SHALL appear; clicking it SHALL always be safe (no-op with a message if there is no Stripe customer yet).

### Requirement: Subscription status badge on Artist changelist
The system SHALL add a read-only "Suscripción" badge to the `ArtistAdmin` changelist showing the `ArtistSubscription.status` display label in Spanish, plus a colored register-style badge variant per state (`pending`, `active`, `past_due`, `canceling`, `canceled`), and the literal "Sin suscripción" when the artist has no subscription row.

#### Scenario: Display without subscription
- **WHEN** an administrator opens the Artist changelist for an artist without an `ArtistSubscription`
- **THEN** the "Suscripción" column SHALL render "Sin suscripción" in muted text.

#### Scenario: Display with active subscription
- **WHEN** an administrator opens the Artist changelist for an artist with `ArtistSubscription.status="active"`
- **THEN** the "Suscripción" column SHALL render a green badge reading "Activa".

#### Scenario: Display during friendly cancellation
- **WHEN** an administrator opens the Artist changelist for an artist with `ArtistSubscription.status="canceling"`
- **THEN** the "Suscripción" column SHALL render an amber badge reading "Cancelada, vigente hasta fin de período".

#### Scenario: Display after lapse
- **WHEN** an administrator opens the Artist changelist for an artist with `ArtistSubscription.status="canceled"` or past-grace `past_due`
- **THEN** the "Suscripción" column SHALL render a red badge reading accordingly.

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

