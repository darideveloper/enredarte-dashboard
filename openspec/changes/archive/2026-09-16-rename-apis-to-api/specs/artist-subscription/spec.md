## MODIFIED Requirements

### Requirement: Public visibility follows subscription state
The system SHALL exclude an artist from the public API (`GET /api/artworks/artists/`) whenever their subscription is not in a paying state — `pending` (link generated, unpaid), `canceled`, or `past_due` past its grace window — by persisting the `compute_is_active` boolean onto `Artist.is_active`, which already drives the public queryset.

#### Scenario: Lapsed artist disappears from the public API
- **WHEN** an artist's subscription becomes `canceled` (or `past_due` past the grace period) and a webhook persists `Artist.is_active=False` via `compute_is_active`
- **THEN** the artist SHALL NOT appear in `GET /api/artworks/artists/`.

#### Scenario: Unpaid pending artist is not listed
- **WHEN** an artist has a `pending` `ArtistSubscription` (link generated, no payment) and no active subscription
- **THEN** the artist SHALL NOT appear in `GET /api/artworks/artists/`.
