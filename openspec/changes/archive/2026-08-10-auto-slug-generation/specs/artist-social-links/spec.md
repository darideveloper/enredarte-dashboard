# Artist Social Links Specification (Delta)

## Purpose

Delta for the `artist-social-links` capability: `ArtistSocialLink` slug auto-generation is refactored to use the shared `unique_slugify` helper. Behavior is unchanged.

## ADDED Requirements

### Requirement: ArtistSocialLink auto-generated slug
The system SHALL auto-generate the `ArtistSocialLink.slug` on save when it is empty, using the shared `unique_slugify` helper with a base of `{artist.slug}-{platform}` and a numeric suffix on collision.

#### Scenario: Auto-generating a link slug
- **WHEN** a social link is saved for an artist with slug `frida-kahlo` and platform `instagram` and no slug is provided
- **THEN** the link slug is set to `frida-kahlo-instagram`.

#### Scenario: Colliding link slugs
- **WHEN** a link with the same artist-platform base already exists
- **THEN** the new link receives a unique suffixed slug (e.g. `frida-kahlo-instagram-1`).

#### Scenario: User-provided slug preserved
- **WHEN** a social link is saved with an explicit slug
- **THEN** the provided slug is kept unchanged.
