# Artist Social Links Specification

## Purpose
To define the `ArtistSocialLink` model that stores multiple typed social network links per artist, its admin inline editing, and seed fixture.

## Requirements

### Requirement: ArtistSocialLink model
The system SHALL provide an `ArtistSocialLink` model in `artworks/models.py` that stores one social network link for an artist, with a typed `platform` value, a `url`, and a `sort_order`.

#### Scenario: Creating a social link
- **WHEN** an administrator saves an `ArtistSocialLink` for an artist with a platform (e.g. Instagram) and a URL
- **THEN** the link is stored and associated with that artist, ordered by `sort_order`.

### Requirement: Multiple social links per artist
The system SHALL allow an artist to have any number of social links, accessed via the `social_links` reverse relation.

#### Scenario: Artist with several links
- **WHEN** an artist has links on Instagram, Facebook, and TikTok
- **THEN** all three links are retrievable from the artist's `social_links` relation, each with its own platform and URL.

### Requirement: Typed social platforms
The system SHALL define a fixed set of platform choices — Instagram, Facebook, X (Twitter), TikTok, LinkedIn, YouTube, Behance, and Other — so the frontend can render per-platform icons.

#### Scenario: Selecting a platform
- **WHEN** an administrator creates a social link
- **THEN** the platform selector only offers the predefined choices and the URL field is validated.

### Requirement: Social links admin inline
The system SHALL expose `ArtistSocialLink` as a sortable `TabularInline` on `ArtistAdmin` with fields `platform`, `url`, and drag-and-drop ordering via `sort_order`.

#### Scenario: Editing links on the artist form
- **WHEN** an administrator opens an Artist edit form
- **THEN** they can add, remove, and reorder the artist's social links without leaving the page.

### Requirement: Seed demo social links
The system SHALL ship a seed fixture `ArtistSocialLink.json` (in `artworks/fixtures/artworks/seed/`) with 2–3 demo links per seeded artist, loaded by `seed_loaddata`.

#### Scenario: Loading demo links
- **WHEN** `seed_loaddata` runs after `base_loaddata`
- **THEN** the seeded artists have 2–3 social links each referencing the seed artist PKs.
