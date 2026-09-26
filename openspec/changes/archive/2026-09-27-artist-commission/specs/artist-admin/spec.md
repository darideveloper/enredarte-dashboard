## MODIFIED Requirements

### Requirement: Artist model admin registration
The system SHALL register the `Artist` model in `artworks/admin.py` using `ModelAdminUnfoldBase` so that artists are manageable within the Django Unfold admin site.

#### Scenario: Viewing artist list in admin
- **WHEN** an administrator opens the Django Admin panel
- **THEN** the sidebar SHALL display "Artistas" with a palette icon and list artists with columns in this order: Name (`display_name`), Commission (`display_commission` formatted as an integer with a percentage symbol e.g., `25%`), Email (`display_email`), Active state (`display_active`), "Suscripción" badge (showing the `ArtistSubscription.status` in Spanish, or "Sin suscripción" when the artist has no subscription row), Obras count, Disponibles count, Galerías count.

#### Scenario: Email is a required field for an active artist to obtain a payment link
- **WHEN** an administrator creates a new `Artist` (or edits an existing one) through the Django Unfold admin form
- **THEN** the `email` field MUST be required (`blank=False`, `null=False`) so the subscription payment-link flow can identify a Stripe customer.

### Requirement: Artist admin form field ordering
The system SHALL organize the `ArtistAdmin` form using `fieldsets` to logically group fields, ensure `slug` directly follows `name`, and include an "Acuerdo comercial" fieldset containing the editable `commission` field.

#### Scenario: Creating or editing an artist
- **WHEN** an administrator views the Artist add or edit form
- **THEN** fields SHALL be organized into logical sections: "Datos personales" (with `slug` positioned immediately after `name`), "Contacto y medios", "Acuerdo comercial" (containing `commission`), "Resumen" (readonly derived blocks), and "Estado del sistema".
