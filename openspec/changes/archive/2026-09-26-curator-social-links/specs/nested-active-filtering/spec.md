## MODIFIED Requirements

### Requirement: Nested collections filter active rows
The system SHALL filter every nested/related collection serialized by the artworks REST API to `is_active=True`, applying the filter both to the through/link rows (when the collection targets `BaseModel`-derived models) and to the target objects. This covers `Artwork.images`, `Artwork.gallery_links`, `Gallery.artwork_links`, `Artist.social_links`, `ArtCurator.social_links`, and the Artwork taxonomy M2Ms (`disciplines`, `techniques`, `themes`, `formats`, `scales`). Inactive rows SHALL never appear inside a nested collection of any API response.

#### Scenario: Inactive artwork images excluded
- **WHEN** an artwork has both active and inactive `ArtworkImage` rows
- **THEN** the artwork detail/list response SHALL include only the active images.

#### Scenario: Inactive gallery links excluded from artwork
- **WHEN** an artwork has an `ArtworkGallery` link to an inactive gallery, or the link row itself is inactive
- **THEN** that link SHALL NOT appear in the artwork's `gallery_links`.

#### Scenario: Inactive artwork links excluded from gallery
- **WHEN** a gallery has an `ArtworkGallery` link to an inactive artwork, or the link row itself is inactive
- **THEN** that link SHALL NOT appear in the gallery's `artwork_links`.

#### Scenario: Inactive social links excluded
- **WHEN** an artist has both active and inactive `ArtistSocialLink` rows
- **THEN** the artist response SHALL include only the active links.

#### Scenario: Inactive curator social links excluded
- **WHEN** a curator has both active and inactive `ArtCuratorSocialLink` rows
- **THEN** the curator response SHALL include only the active links.

#### Scenario: Inactive taxonomy refs excluded
- **WHEN** an active artwork references an inactive taxonomy term (e.g. a `Discipline` with `is_active=False`)
- **THEN** that term SHALL NOT appear in the artwork's corresponding ref array.
