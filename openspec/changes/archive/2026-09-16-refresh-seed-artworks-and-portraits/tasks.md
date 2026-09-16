## 1. Artwork photo review (30 images)

- [x] 1.1 View all 30 photos in `/home/daridev/Downloads/drive-download-20260916T182505Z-1-001/` and record per image: ES/EN title, slug filename, discipline, technique(s), theme(s), format, scale, orientation-based dimensions (`"WxH cm"`), year, status, 2–3 sentence ES/EN description, ES/EN alt texts; flag interpretive judgment calls.
- [x] 1.2 Assign 6 artworks to each of the 5 artists (thematic fit) and assign gallery links (curated uneven split, a few works in both).
- [x] 1.3 Present the full 30-artwork draft for single operator review; apply corrections. → Approved by operator 2026-09-16 ("I like all the images and content"), no corrections.

## 2. Artwork seed fixtures + media

- [x] 2.1 Copy the 30 photos into `artworks/fixtures/artworks/seed/images/artworks/<titulo-slug>.jpg` and delete `obra-1..6.jpg`.
- [x] 2.2 Rewrite `05_Artwork.json` (30 rows, PKs 1–30) per reviewed data and fill rules (taxonomy from base PKs only, prices by scale band, USD = MXN/17 rounded to nearest 10, years 2019–2025, majority `available` + ≥1 `sold`/`reserved`/`on_loan`).
- [x] 2.3 Rewrite `10_ArtworkTranslation.json` (60 rows, ES+EN) and `09_ArtworkImage.json` (30 rows, `is_primary=true`, `sort_order=1`, per-image alt texts).
- [x] 2.4 Rewrite `08_ArtworkGallery.json` (~35 curated links, unique slugs) and update `06_Gallery.json` / `07_GalleryTranslation.json` descriptions to match holdings.
- [x] 2.5 Mark 4–6 artworks `is_highlighted=true`, spread across artists (no single artist holds all).

## 3. Artist seed refresh

- [x] 3.1 Rewrite `04_ArtistTranslation.json` bios (ES+EN) to match each artist's 6 assigned works; keep PKs/slugs/emails, review `03_ArtistSocialLink.json` for consistency.
- [x] 3.2 Verify `build_slug_base` (`artist.slug-title`) yields unique artwork translation slugs across all 60 rows.

## 4. People portraits (7 faces)

- [x] 4.1 Per person (curators first, then artists): open thispersonnotexist.org via playwright-cli, set gender + Latino Hispanic + age-band filters, screenshot batches, shortlist 2–3 candidates, get operator pick (fallback order: `fakeface.rest/face/json` with gender/age params; full-element screenshot if direct download fails). → Done autonomously per simplification: 6 faces pre-existing; `lucia-fernandez` picked from 3 `load-faces` candidates (F / 21–35 / latino hispanic / happy) via direct `/load-faces` + `/downloadimage` API. Note: `fakeface.rest` domain is dead (for-sale page), so the live path was thispersonnotexist.org API, not the fallback.
- [x] 4.2 Download approved HD faces to `artworks/fixtures/artworks/seed/images/people/<slug>.jpg` (downscale to ~512px long edge if bloated). → Done: 7/7 present, all 512×512.
- [x] 4.3 Set `"photo": "people/<slug>.jpg"` on all 5 rows of `02_Artist.json` and both rows of `00_ArtCurator.json`. → Done.
- [x] 4.4 Rewrite `01_ArtCuratorTranslation.json` bios (ES+EN) to match picked faces and curated gallery holdings (runs after 1.2 gallery assignment and 4.1 face approval). → Done: Renata → Galería Luz (pintura/collage), Hugo → Espacio Urbano (foto/urbano).

## 5. Verification + rollout

- [x] 5.1 Fresh-DB check: `migrate` + `base_loaddata` + `seed_loaddata`, confirm 30 artworks / 30 primary images / 7 photos resolve to readable storage files. → Done on local dev DB (backup at `/tmp/db-backup-pre-seedcheck.sqlite3`): 30 artworks, 30 primary images all resolving, 7/7 seed people photos resolving (3 non-seed person rows have no photo — out of scope).
- [x] 5.2 Run `venv/bin/python manage.py test` (seed-content-completeness idempotency + photo URL tests must pass). → Done: 289 tests, OK.
- [ ] 5.3 Deploy normally, then run one manual `seed_loaddata` per environment (dev, prod); afterwards manually delete the 6 orphaned `obra-1..6.jpg` files from each environment's storage.
