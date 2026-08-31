## MODIFIED Requirements

### Requirement: Artist model admin registration
The system SHALL register the `Artist` model in `artworks/admin.py` using `ModelAdminUnfoldBase` so that artists are manageable within the Django Unfold admin site.

#### Scenario: Viewing artist list in admin
- **WHEN** an administrator opens the Django Admin panel
- **THEN** the sidebar SHALL display "Artistas" with a palette icon and list artists with columns for Name, Email, Birth Year, Death Year, Active state, and a "Suscripción" badge column showing the `ArtistSubscription.status` in Spanish (or "Sin suscripción" when the artist has no subscription row).

#### Scenario: Email is a required field for an active artist to obtain a payment link
- **WHEN** an administrator creates a new `Artist` (or edits an existing one) through the Django Unfold admin form
- **THEN** the `email` field MUST be required (`blank=False`, `null=False`) so the subscription payment-link flow can identify a Stripe customer.

## ADDED Requirements

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
