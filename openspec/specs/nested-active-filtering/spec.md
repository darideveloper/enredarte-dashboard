# Nested Active Filtering Specification

## Purpose

This specification defines the system-wide behavior for filtering inactive rows from nested/related collections and resolving single-ForeignKey references to `null` when the referenced row is inactive. It covers all nested data serialized by the artworks REST API.

## Requirements

### Requirement: Nested collections filter active rows
The system SHALL filter every nested/related collection serialized by the artworks REST API to `is_active=True`, applying the filter both to the through/link rows (when the collection targets `BaseModel`-derived models) and to the target objects. This covers `Artwork.images`, `Artwork.gallery_links`, `Gallery.artwork_links`, `Artist.social_links`, and the Artwork taxonomy M2Ms (`disciplines`, `techniques`, `themes`, `formats`, `scales`). Inactive rows SHALL never appear inside a nested collection of any API response.

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

#### Scenario: Inactive taxonomy refs excluded
- **WHEN** an active artwork references an inactive taxonomy term (e.g. a `Discipline` with `is_active=False`)
- **THEN** that term SHALL NOT appear in the artwork's corresponding ref array.

### Requirement: Inactive single-FK refs resolve to null
The system SHALL serialize single-ForeignKey references as `null` when the referenced row is inactive, for `Artist.location` and `Gallery.curator`.

#### Scenario: Artist with inactive location
- **WHEN** an active artist references a `Location` with `is_active=False`
- **THEN** the artist's `location` field SHALL be `null`.

#### Scenario: Gallery with inactive curator
- **WHEN** an active gallery references an `ArtCurator` with `is_active=False`
- **THEN** the gallery's `curator` field SHALL be `null`.

#### Scenario: Active refs keep current shape
- **WHEN** the referenced row is active
- **THEN** the field SHALL remain the `{id, slug}` ref object.

### Requirement: Artworks with inactive artists are excluded
The system SHALL exclude artworks whose `artist` is inactive from the artworks list and detail endpoints, so a deactivated artist's works never appear in the API.

#### Scenario: Artwork of inactive artist hidden
- **WHEN** an artwork is active but its `artist` has `is_active=False`
- **THEN** the artwork SHALL NOT appear in the artworks list endpoint.
- **AND** a detail request for that artwork SHALL return a 404 error envelope.

#### Scenario: Artwork of active artist remains
- **WHEN** an artwork's `artist` is active
- **THEN** the artwork SHALL appear in the artworks list endpoint with its `artist` `{id, slug}` ref.
