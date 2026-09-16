## Context

Seed fixtures live per-app (`artworks/fixtures/artworks/seed/*.json`, loaded PK-ordered by `seed_loaddata`), with committed sample media under `seed/images/` synced into default storage (local `MEDIA_ROOT` or S3) on a skip-if-exists basis. Current artworks seed: 6 dummy artworks with `obra-N.jpg` images, 5 artists and 2 curators with **no** `photo` values (field exists on `Person`, `core/models.py:105`, no `upload_to`), 2 galleries with 8 artwork links. Thirty real artwork photos (1920px long edge, ~50MB) sit outside the repo at `/home/daridev/Downloads/drive-download-20260916T182505Z-1-001/`. Two sibling changes are in progress: `add-artwork-stripe-sales` (consumes `price_mxn/usd`) and `-artwork-mockups` (parses `dimensions` strings into `width_cm/height_cm`).

## Goals / Non-Goals

**Goals:**
- 30 real artworks with per-image grounded data (title, taxonomy, dimensions, price, year, status, ES/EN texts).
- Portrait photo on all 5 artists + 2 curators, user-approved face by face.
- Galleries/artists seed rewritten to cohere with the new catalog; everything loads via one `seed_loaddata` run and stays idempotent.

**Non-Goals:**
- No model, migration, serializer, admin, or API changes.
- No new taxonomy rows (base data frozen); no blog seed changes.
- No mockup generation or Stripe wiring — those changes consume this data as-is.

## Decisions

- **30 artworks × 1 primary image** (over 6×5 views or ~12 series): each photo is a distinct work, so 1:1 is the only honest mapping. Alternative grouping into series rejected — the photos are unrelated subjects.
- **Keep 5 artist PKs/slugs, 6 works each, bios rewritten**: preserves FK stability (`Artwork.artist`, social links, translation slug base `artist.slug-title`) while making bios match assigned works. Minting new artists rejected as churn with no functional gain.
- **Curated uneven gallery split** (over 15/15 or all-in-both): thematic assignment (e.g. Luz→painting/illustration, Urbano→photo/street-art) with a few works in both; gallery descriptions rewritten around holdings.
- **Filenames = Spanish title slug** (`<titulo-slug>.jpg`, over iStock IDs or `obra-07..30`): human-meaningful, matches existing slug conventions. Old `obra-1..6.jpg` deleted from git.
- **Portraits from thispersonnotexist.org** (over dead thispersondoesnotexist.com, over `fakeface.rest` API): alive, free commercial use, no signup/throttle, and uniquely offers **Latino-Hispanic race filter + age bands**, which is exactly the matching criteria. `fakeface.rest` stays as fallback (gender+age only). Candidates-per-person approval (over autonomous pick): faces are subjective, user wants the call.
- **`dimensions` strictly `"WxH cm"` / `"WxHxD cm"`**: hard constraint from `-artwork-mockups` parser. Physical sizes inferred from aspect ratio (landscape→wide, portrait→tall, square→square) within plausible bands.
- **Curator bios rewritten to match faces** (over photos-only): faces are picked on assumed age bands, so leaving dummy bios risks a face/bio mismatch; rewriting both ES/EN bios around the picked face + curated holdings closes the loop. Pulls `01_ArtCuratorTranslation.json` into scope.
- **4–6 artworks flagged `is_highlighted`, spread across artists** (over all-false default): the artist-profile "Destacados" block would otherwise render empty in demo; one per artist + extras is seed-only data with no logic impact.
- **Orphaned `obra-*.jpg` deleted manually per storage** (over leaving them): 6 orphan files per environment; explicit deletion keeps storages clean. Rollout task, post-seed.
- **Prices banded-random by scale** (mini 8–25k MXN, gran formato 40–140k MXN, USD≈MXN/17): plausible for Stripe checkout realism without pretending to appraise.
- **Portraits at `seed/images/people/<slug>.jpg`**, fixture `"photo": "people/<slug>.jpg"`: new subfolder keeps seed media organized; relative path flows through existing `_sync_seed_media` untouched.

## Risks / Trade-offs

- [Repo bloat ~50MB committed seed media] → Accepted; documented in proposal. Mitigation: images already web-sized (1920px); portraits downscaled to ~512px.
- [iStock photos are depictions, not artworks — technique/discipline is interpretive] → Mitigation: judgment calls flagged in the single review pass for correction, not silently baked in.
- [Re-running `seed_loaddata` on prod UPDATES PKs 1–6 in place] → That is the intended deploy mechanism here (one run), not repeated runs. Documented; orphaned `obra-*.jpg` in storage left alone with optional-cleanup note.
- [Artist birth years vs picked faces] → Faces are picked against current birth years; if a later change rewrites ages, fit must be re-checked (noted as follow-up, not handled here).
- [fakeface/thispersonnotexist.org availability] → Both verified HTTP 200 at proposal time; downloads committed to git immediately so future outages don't matter.

## Migration Plan

1. Land fixture + media changes on a dev checkout; run `seed_loaddata` on a **fresh** DB; run `manage.py test` (completeness tests assert non-empty + idempotent).
2. Deploy normally (entrypoint runs only `base_loaddata` — no seed impact).
3. One manual `python manage.py seed_loaddata` per environment (dev, prod) to insert PKs 7–30 / update 1–6 and sync new media, then manually delete the 6 orphaned `obra-*.jpg` files from each environment's storage. Rollback = re-run previous fixture set (git) + one `seed_loaddata`; orphaned new files remain in storage harmlessly.

## Open Questions

None open — all resolved during proposal review: price bands/years accepted as specced, `obra-*.jpg` orphans deleted manually per storage, curator bios rewritten to match faces, 4–6 works flagged `is_highlighted`. Artwork data reviewed in one all-30 pass; faces approved candidate-by-candidate via chat screenshots.
