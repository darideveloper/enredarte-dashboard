## ADDED Requirements

### Requirement: Artist commission visibility in sales order admin
The system SHALL display the selling artist's commission percentage as a read-only field (`display_artist_commission`) in the `ArtworkOrderAdmin` change view within `fieldsets` and `readonly_fields`. When an order is associated with an artwork and artist, the field SHALL render the commission percentage formatted with a percentage symbol (e.g. `25%`); if the artwork, artist, or commission is unset, it SHALL display `-`.

#### Scenario: Viewing sales order displays artist commission
- **WHEN** an administrator opens the change view for an `ArtworkOrder` whose sold artwork belongs to an artist with a commission rate of 25%
- **THEN** the "Comisión del artista" read-only field SHALL display `25%`.

#### Scenario: Viewing order with unset artist or commission
- **WHEN** an administrator views an `ArtworkOrder` where the artist or commission is not set
- **THEN** the "Comisión del artista" read-only field SHALL display `-`.
