# Artist Social Links — Delta

Delta spec for the `artist-social-links` capability.

## MODIFIED Requirements

### Requirement: ArtistSocialLink model
The system SHALL provide an `ArtistSocialLink` model in `artworks/models.py` that stores one social network link for an artist, with a typed `platform` value and a `url`. The model SHALL NOT have a `sort_order` field and SHALL NOT define default ordering.

#### Scenario: Creating a social link
- **WHEN** an administrator saves an `ArtistSocialLink` for an artist with a platform (e.g. Instagram) and a URL
- **THEN** the link is stored and associated with that artist.

#### Scenario: Social link has no sort_order
- **WHEN** the `ArtistSocialLink` model is inspected
- **THEN** it SHALL NOT expose a `sort_order` field in its schema, admin inline, or serialized output.

### Requirement: Social links admin inline
The system SHALL expose `ArtistSocialLink` as a `TabularInline` on `ArtistAdmin` with fields `platform` and `url`. The inline SHALL NOT use `sort_order`-based drag-and-drop ordering.

#### Scenario: Editing links on the artist form
- **WHEN** an administrator opens an Artist edit form
- **THEN** they can add and remove the artist's social links without leaving the page.