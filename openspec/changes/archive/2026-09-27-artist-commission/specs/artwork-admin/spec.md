## ADDED Requirements

### Requirement: Artist commission visibility in artwork admin
The system SHALL display the assigned artist's commission percentage as a read-only field (`display_artist_commission`) in the `ArtworkAdmin` change view within `fieldsets` and `readonly_fields`. When an artwork has an assigned artist, the field SHALL display the commission formatted with a percentage symbol (e.g. `25%`); if the artist has no commission or is unset, it SHALL display `-`.

#### Scenario: Viewing artwork detail displays artist commission
- **WHEN** an administrator opens the change view for an Artwork whose artist has a commission of 25%
- **THEN** the "Comisión del artista" read-only field SHALL display `25%`.

#### Scenario: Viewing artwork with unset artist or commission
- **WHEN** an administrator opens an Artwork without an assigned artist or with an unset commission
- **THEN** the "Comisión del artista" read-only field SHALL display `-`.
