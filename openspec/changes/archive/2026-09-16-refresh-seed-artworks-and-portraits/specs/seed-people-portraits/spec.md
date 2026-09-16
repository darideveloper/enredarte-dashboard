## ADDED Requirements

### Requirement: Every seed artist and curator has a portrait photo

Each seeded `Artist` (5) and `ArtCurator` (2) SHALL have a `photo` value pointing at a committed seed media file under `seed/images/people/`, so no profile renders imageless.

#### Scenario: Portraits load into readable storage files
- **WHEN** `seed_loaddata` runs on a fresh database that already ran `base_loaddata`
- **THEN** every `Artist` and `ArtCurator` row has a non-empty `photo`, and each referenced file exists in the configured default storage (written from committed seed images).

#### Scenario: Portrait files are web-sized headshots
- **WHEN** the seed media directory is inspected
- **THEN** `seed/images/people/` holds 7 `<person-slug>.jpg` files, each a single-face headshot roughly 512px on the long edge.

### Requirement: Portraits are AI faces matched per person with approval

Portrait images SHALL be synthetic faces (no real persons) sourced from thispersonnotexist.org (fallback: fakeface.rest), selected with gender + Latino-Hispanic + age-band filters appropriate to each person, with 2–3 candidates shown per person and the final pick approved by the operator before committing.

#### Scenario: Filter criteria per person
- **WHEN** portrait candidates are gathered
- **THEN** Mariana Ríos uses Female / 35-50, Diego Morales Male / 50+, Valentina Cruz Female / 21-35, Santiago Herrera Male / 50+, Lucía Fernández Female / 35-50, Renata Ortega Female / 35-50, Hugo Salinas Male / 35-50 — all with race Latino Hispanic.

#### Scenario: No pick is committed unapproved
- **WHEN** the portrait set is finalized
- **THEN** each of the 7 files corresponds to an operator-approved candidate, recorded with its source and filter settings.

### Requirement: Curator bios match faces and holdings

Both seeded curators SHALL have rewritten ES/EN bios in `ArtCuratorTranslation` that are consistent with their approved portrait (apparent age, presentation) and the galleries they curate, so no face/bio mismatch ships.

#### Scenario: Bios rewritten after faces are picked
- **WHEN** curator translation rows are inspected after the portrait round
- **THEN** each curator has both `es` and `en` rows whose bio text is consistent with the picked portrait and references the galleries they curate.
