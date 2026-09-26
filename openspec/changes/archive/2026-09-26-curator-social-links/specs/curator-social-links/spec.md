## Purpose

Defines the `ArtCuratorSocialLink` model and shared `BaseSocialLink` abstract model to store typed social network links for art curators, with auto-generated slugs and seed demo fixtures.

## ADDED Requirements

### Requirement: ArtCuratorSocialLink model
The system SHALL provide an `ArtCuratorSocialLink` model in `artworks/models.py` inheriting from a shared `BaseSocialLink` abstract model. The model SHALL store one social network link for an art curator, with a foreign key to `ArtCurator`, a typed `platform` value, and a `url`. The model SHALL NOT have a `sort_order` field and SHALL NOT define default ordering.

#### Scenario: Creating a curator social link
- **WHEN** an administrator saves an `ArtCuratorSocialLink` for a curator with a platform and a URL
- **THEN** the link is stored and associated with that curator.

#### Scenario: Curator social link has no sort_order
- **WHEN** the `ArtCuratorSocialLink` model is inspected
- **THEN** it SHALL NOT expose a `sort_order` field in its schema, admin inline, or serialized output.

### Requirement: Multiple social links per curator
The system SHALL allow a curator to have any number of social links, accessed via the `social_links` reverse relation.

#### Scenario: Curator with several links
- **WHEN** a curator has links on Instagram, LinkedIn, and X
- **THEN** all three links are retrievable from the curator's `social_links` relation, each with its own platform and URL.

### Requirement: Shared typed social platforms
The system SHALL define a shared set of platform choices on `BaseSocialLink.Platform` — Instagram, Facebook, X (Twitter), TikTok, LinkedIn, YouTube, Behance, and Other — used by both `ArtistSocialLink` and `ArtCuratorSocialLink`.

#### Scenario: Selecting a platform for a curator
- **WHEN** an administrator creates a curator social link
- **THEN** the platform selector offers the predefined choices with localized Spanish display labels.

### Requirement: ArtCuratorSocialLink auto-generated slug
The system SHALL auto-generate the `ArtCuratorSocialLink.slug` on save when it is empty, using the shared `unique_slugify` helper with a base of `{curator.slug}-{platform}` and a numeric suffix on collision.

#### Scenario: Auto-generating a curator link slug
- **WHEN** a social link is saved for a curator with slug `renata-ortega` and platform `instagram` and no slug is provided
- **THEN** the link slug is set to `renata-ortega-instagram`.

#### Scenario: Colliding curator link slugs
- **WHEN** a link with the same curator-platform base already exists
- **THEN** the new link receives a unique suffixed slug (e.g. `renata-ortega-instagram-1`).

#### Scenario: Preserving user-provided slug
- **WHEN** a social link is saved with an explicit slug
- **THEN** the provided slug is kept unchanged.

### Requirement: Seed demo curator social links
The system SHALL provide a seed fixture `01b_ArtCuratorSocialLink.json` (in `artworks/fixtures/artworks/seed/`) with demo links for seeded curators, loaded by `seed_loaddata`.

#### Scenario: Loading demo curator links
- **WHEN** `seed_loaddata` runs after curator fixtures are loaded
- **THEN** the seeded curators have demo social links referencing the seed curator PKs.
