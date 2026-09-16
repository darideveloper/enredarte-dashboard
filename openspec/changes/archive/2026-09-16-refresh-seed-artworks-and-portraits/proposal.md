## Why

The seed catalog still ships placeholder content: 6 dummy artworks (`obra-1..6.jpg`), 5 dummy artists and 2 curators with no profile photos, and invented prices/descriptions. The dashboard is approaching demo/sales readiness (Stripe artwork sales and mockups changes in progress), and dummy seed data undermines catalog, artist-profile, and checkout flows. Thirty real, resized artwork photos are already prepared locally, and AI-generated portrait sources are verified — so the seed can be rebuilt around real media now.

## What Changes

- Replace the 6 dummy artwork images with 30 real artwork photos (long edge 1920px, already resized), stored as `seed/images/artworks/<titulo-slug>.jpg`; delete `obra-1..6.jpg` from the repo.
- Rewrite artwork seed fixtures to 30 artworks (PKs 1–30, 1 primary image each): ES/EN titles, descriptions, alt texts, taxonomy classification within existing base vocab, `dimensions` in `"WxH cm"` parseable format, banded-random prices, years 2019–2025, mixed availability statuses.
- Rewrite artist seed data (same 5 PKs/slugs): redistribute to exactly 6 works each, rewrite ES/EN bios to match assigned works; keep social links.
- Rewrite gallery seed links as a curated uneven split across the 2 existing galleries (a few works in both); rewrite gallery descriptions to match holdings.
- Rewrite curator ES/EN bios to match picked faces and gallery holdings.
- Add profile portraits for all 5 artists + 2 curators: AI-generated faces (StyleGAN, free commercial use) browsed with gender + Latino-Hispanic + age filters, approved candidate-by-candidate, stored as `seed/images/people/<slug>.jpg` and referenced via `Person.photo` (no migration — field exists).
- One `seed_loaddata` re-run (dev + prod) picks up the new seed: inserts new PKs, updates PKs 1–6 by PK, syncs new media files, skips existing files. Orphaned `obra-*.jpg` copies in existing storages are deleted manually from each storage after the seed run (rollout task).

## Capabilities

### New Capabilities

- `seed-artwork-catalog`: 30 real artworks grown from reviewed photos — per-image title/slug/filename, taxonomy mapping, dimensions format, price/year/status rules, ES/EN translations and alt texts.
- `seed-people-portraits`: portrait photo for every seed artist and curator — source, filter criteria per person, approval workflow, file location and fixture wiring.

### Modified Capabilities

- `seed-content-completeness`: seed volume expectations change (6→30 artworks, 6→30 artwork images, ~35 gallery links, 7 portrait photos added); idempotent re-load and non-empty-table guarantees still hold.

## Impact

- Files: `artworks/fixtures/artworks/seed/{02_Artist,04_ArtistTranslation,05_Artwork,08_ArtworkGallery,09_ArtworkImage,10_ArtworkTranslation}.json`, `06_Gallery.json` + `07_GalleryTranslation.json` (descriptions), `00_ArtCurator.json` (photo) + `01_ArtCuratorTranslation.json` (bios rewritten to match faces), 30 new + 7 new seed media files, 6 deleted dummy files.
- No model/migration/API changes. Public catalog, artist-profile, and gallery endpoints serve the new content unchanged; Stripe sales change consumes the new prices as-is.
- Coordinated with in-progress `add-artwork-stripe-sales` (prices feed checkout) and `-artwork-mockups` (`dimensions` strings must stay parser-compatible: `"120x90 cm"` / `"45x30x20 cm"`).
- Repo grows by ~50MB of committed seed media (accepted trade-off; documented).
