## MODIFIED Requirements

### Requirement: Artist model admin registration
The system SHALL register the `Artist` model in `artworks/admin.py` using `ModelAdminUnfoldBase` so that artists are manageable within the Django Unfold admin site.

#### Scenario: Viewing artist list in admin
- **WHEN** an administrator opens the Django Admin panel
- **THEN** the sidebar SHALL display "Artistas" with a palette icon and list artists with columns in this order: Name, Email, Active state, "Suscripción" badge (showing the `ArtistSubscription.status` in Spanish, or "Sin suscripción" when the artist has no subscription row), Obras count, Disponibles count, Galerías count.

#### Scenario: Email is a required field for an active artist to obtain a payment link
- **WHEN** an administrator creates a new `Artist` (or edits an existing one) through the Django Unfold admin form
- **THEN** the `email` field MUST be required (`blank=False`, `null=False`) so the subscription payment-link flow can identify a Stripe customer.

### Requirement: Changelist summary columns on Artist admin
The system SHALL render exactly three readonly count columns on the `ArtistAdmin` changelist — artworks (`display_artworks_count`), available works (`display_available_count`), and galleries (`display_galleries_count`) — computed from the `Artist` derived properties (see `artist-derived-fields`). Techniques and highlighted-work counts SHALL remain available in the readonly "Resumen" fieldset on the change form, not as changelist columns. `birth_year` and `death_year` SHALL NOT appear as changelist columns (detail form only).

#### Scenario: Viewing artist counts
- **WHEN** an administrator opens the Artist changelist
- **THEN** each row shows the computed counts for artworks, available works, and galleries, positioned after the "Suscripción" badge column.
