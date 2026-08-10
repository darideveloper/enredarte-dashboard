## MODIFIED Requirements

### Requirement: Seed fixture loading command
The system SHALL provide a `seed_loaddata` management command that scans every app's `<app>/fixtures/<app>/seed/` directory and loads each JSON fixture the same fail-soft way, used for one-time demo content and never invoked from the Docker build. Seed fixture filenames SHALL be prefixed with zero-padded numeric prefixes so that sorted (alphabetical) load order matches cross-fixture dependencies (dependencies load before dependents). Before loading fixtures, the command SHALL write any committed sample media files found under each app's `seed/images/` directory into the configured default storage (local `MEDIA_ROOT` or remote bucket) via the storage API, so seeded image records reference readable files in every environment; files that already exist in storage SHALL be left untouched.

#### Scenario: Loading demo content once
- **WHEN** `seed_loaddata` runs on an environment that has run `base_loaddata`
- **THEN** the sample artists and artworks referenced in `seed/` fixtures are created with taxonomy references resolving to the seeded base rows.

#### Scenario: Deterministic cross-fixture load order
- **WHEN** seed fixtures include rows referencing other seed models (e.g. `ArtworkGallery` referencing `Gallery`)
- **THEN** the numeric prefixes ensure the referenced model's fixture loads first, so no dependency row is silently dropped by the fail-soft loop on first run.

#### Scenario: Seed media files synced to the default storage
- **WHEN** `seed_loaddata` runs and a committed image exists under `seed/images/`
- **THEN** the file is written into the configured default storage (local `MEDIA_ROOT` or S3 bucket) under its relative path before the fixtures are loaded, and already-present files are left untouched.

#### Scenario: Seed loading excluded from builds
- **WHEN** the Dockerfile or `start.sh` sets up an environment
- **THEN** only `base_loaddata` runs; `seed_loaddata` is not part of the build pipeline.
