## MODIFIED Requirements

### Requirement: ArtistSubscription admin registration
The system SHALL register `ArtistSubscription` in the Django Unfold admin so an operator can browse and search subscriptions: list by `artist`, filter by `status` (`pending`/`active`/`past_due`/`canceling`/`canceled`), filter by `payment_method` (`online`/`cash`), filter by `is_active_of_artist` and show `created_at` / `last_synced_at`. The admin MUST support searching by `artist__name` and `stripe_subscription_id`.

#### Scenario: Filtering subscriptions by status
- **WHEN** an administrator opens the "Suscripciones de artistas" admin and selects a `status` filter
- **THEN** only `ArtistSubscription` rows in that status SHALL be shown.

#### Scenario: Filtering subscriptions by payment method
- **WHEN** an administrator opens the "Suscripciones de artistas" admin and selects a `payment_method` filter (`En línea` / `Efectivo`)
- **THEN** only `ArtistSubscription` rows with that payment method SHALL be shown.

#### Scenario: Searching for an artist by subscription id
- **WHEN** an administrator types a Stripe subscription id in the admin search box
- **THEN** the `ArtistSubscription` row with that `stripe_subscription_id` SHALL be the only row that matches.
