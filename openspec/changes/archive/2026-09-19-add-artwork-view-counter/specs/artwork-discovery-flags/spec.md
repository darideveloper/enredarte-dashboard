## MODIFIED Requirements

### Requirement: Views counter on Artwork
The system SHALL keep `Artwork.views_count` (`PositiveIntegerField`, default `0`) as the visit counter incremented by the public artwork view-tracking endpoint (`POST artworks/{slug}/visit/`); it SHALL remain editable in the admin so values can be seeded manually.

#### Scenario: Tracking views
- **WHEN** an anonymous `POST` hits the artwork visit endpoint
- **THEN** the artwork's `views_count` SHALL increment by 1 and the artist's "most viewed" block SHALL order works by this field descending.

#### Scenario: Manual counter seeding
- **WHEN** an administrator edits an artwork
- **THEN** they can set `views_count` directly.
