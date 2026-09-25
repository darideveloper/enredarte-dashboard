## MODIFIED Requirements

### Requirement: Subscription action buttons on Artist edit view
The system SHALL render three admin actions on the `ArtistAdmin` change view (next to the existing fieldset buttons), available only to staff: "Generar / Regenerar link de suscripción", "Abrir Customer Portal", and "Sincronizar desde Stripe". The buttons SHALL be wired to the corresponding endpoints declared in `specs/subscription-admin-controls/spec.md`. These are **artist-membership** controls: they SHALL remain hosted on `ArtistAdmin` in `artworks/admin.py` and SHALL continue to consume subscription-domain services (`subscriptions.services.stripe_client`, `subscription_state`, `notifications`, `subscriptions.models`) after the artwork-sales refactor. Moving them is explicitly out of scope; only sale-shaped code leaves `subscriptions`, so the "no subscription imports in artworks sale modules" rule does not apply to this admin.

#### Scenario: "Generar / Regenerar link" button is present
- **WHEN** an administrator opens an `Artist` change page
- **THEN** a button labelled "Generar link de suscripción" (or "Regenerar link" when an existing subscription's signup URL has expired) SHALL appear in the actions bar.

#### Scenario: "Abrir Customer Portal" button visible when relevant
- **WHEN** an administrator opens an `Artist` change page for an artist whose `ArtistSubscription.stripe_customer_id` is non-empty
- **THEN** a button labelled "Abrir Customer Portal" SHALL appear; clicking it SHALL trigger the endpoint from `specs/subscription-admin-controls/spec.md` and reveal the portal URL inline.

#### Scenario: "Sincronizar desde Stripe" button always available
- **WHEN** an administrator opens an `Artist` change page
- **THEN** a "Sincronizar desde Stripe" button SHALL appear; clicking it SHALL always be safe (no-op with a message if there is no Stripe customer yet).

#### Scenario: Membership controls unaffected by the sale refactor
- **WHEN** the artwork-sales refactor is applied
- **THEN** the three subscription actions SHALL still render and function on the `Artist` change page, and `artworks/admin.py` SHALL still import the subscription-domain services that back them.
