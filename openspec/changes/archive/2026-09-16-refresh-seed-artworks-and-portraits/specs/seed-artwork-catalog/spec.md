## ADDED Requirements

### Requirement: Seed catalog holds thirty real artworks

The system SHALL ship 30 `Artwork` seed rows (PKs 1–30), each with exactly one primary `ArtworkImage`, grown from individually reviewed photos — no placeholder rows remain.

#### Scenario: Thirty artworks with one primary image each
- **WHEN** `seed_loaddata` runs on a fresh database that already ran `base_loaddata`
- **THEN** the `Artwork` table contains 30 rows and the `ArtworkImage` table contains 30 rows, each artwork having exactly one image with `is_primary=true` and `sort_order=1`.

#### Scenario: No dummy artwork media remains in repo
- **WHEN** the seed media directory is inspected
- **THEN** `seed/images/artworks/` contains 30 `<titulo-slug>.jpg` files and none of `obra-1.jpg`…`obra-6.jpg`.

### Requirement: Artwork data is grounded per image with random fill for the rest

Each seeded artwork SHALL carry data derived from its reviewed photo where inferable (title, taxonomy, orientation-based dimensions, bilingual descriptions and alt texts) and randomly filled where not (price within scale band, year, status), following fixed rules.

#### Scenario: Taxonomy uses only existing base rows
- **WHEN** any seeded `Artwork` row is inspected
- **THEN** its `disciplines`, `techniques`, `themes`, `formats`, and `scales` reference only PKs already present in base fixtures (6 disciplines, 7 techniques, 15 themes, 6 formats, 2 scales).

#### Scenario: Dimensions stay mockup-parser compatible
- **WHEN** any seeded `Artwork.dimensions` value is inspected
- **THEN** it matches `"WxH cm"` or `"WxHxD cm"` with integer values (e.g. `"120x90 cm"`), parseable by the `-artwork-mockups` dimension backfill.

#### Scenario: Prices, years, and statuses follow the fill rules
- **WHEN** seeded `Artwork` rows are inspected
- **THEN** `price_mxn` falls in 8,000–25,000 for `mini-obras` scale or 40,000–140,000 for `gran-formato` scale, `price_usd` equals `price_mxn / 17` rounded to the nearest 10, `year` falls in 2019–2025, and statuses include a majority of `available` with at least one `sold`, one `reserved`, and one `on_loan`.

#### Scenario: Bilingual texts reference the visible content
- **WHEN** a seeded `ArtworkTranslation` or `ArtworkImage` row is inspected
- **THEN** it has both `es` and `en` rows whose title, description, and alt texts describe what is visible in the photo (not generic filler), and the image filename equals the slugified Spanish title.

### Requirement: Artists each hold six works with matching bios

The 5 seeded artists (unchanged PKs/slugs) SHALL each be referenced by exactly 6 artworks, and their ES/EN bios SHALL describe practices consistent with their assigned works.

#### Scenario: Even artwork distribution
- **WHEN** artworks per artist are counted after seeding
- **THEN** each of the 5 artists holds exactly 6 artworks.

### Requirement: Galleries show a curated split

Seeded `ArtworkGallery` links SHALL place every artwork in at least one gallery, split thematically and unevenly across the 2 galleries, with a few works in both; gallery ES/EN descriptions SHALL reflect their holdings.

#### Scenario: Full curated coverage
- **WHEN** gallery links are inspected after seeding
- **THEN** all 30 artworks appear in at least one gallery, the two galleries hold different counts, at least one artwork appears in both, and each link carries a unique `slug`.

### Requirement: Highlighted works populate the Destacados block

Between 4 and 6 seeded artworks SHALL have `is_highlighted=true`, spread across artists, so artist-profile "Destacados" blocks render content in demo.

#### Scenario: Highlights spread across artists
- **WHEN** highlighted artworks are counted after seeding
- **THEN** 4–6 artworks have `is_highlighted=true`, no single artist holds all of them, and every highlighted artwork is `is_active=true`.
