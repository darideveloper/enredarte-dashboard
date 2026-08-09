# Fixture Loading Specification

## Purpose
To define the requirements for the `base_loaddata` and `seed_loaddata` management commands that load base and seed fixtures across installed apps, and how they are wired into environments.

## Requirements

### Requirement: Base fixture loading command
The system SHALL provide a `base_loaddata` management command that auto-discovers every `<app>/fixtures/<app>/` directory across all installed apps and, in sorted (alphabetical) order, loads each `*.json` fixture via Django's `loaddata`, wrapped in a fail-soft `try/except` that prints the error and continues on failure.

#### Scenario: Fresh environment loads all base taxonomies
- **WHEN** `base_loaddata` runs on a fresh database
- **THEN** every base fixture from every installed app (including the five artwork taxonomy files) is loaded by the referenced FK PKs, without aborting the whole run.

#### Scenario: Fail-soft on duplicate keys
- **WHEN** an already-loaded fixture is encountered (e.g. re-running on a populated DB)
- **THEN** the error is printed, the row's load is skipped, and the remaining fixtures still attempt to load.

### Requirement: Seed fixture loading command
The system SHALL provide a `seed_loaddata` management command that scans every app's `<app>/fixtures/<app>/seed/` directory and loads each JSON fixture the same fail-soft way, used for one-time demo content and never invoked from the Docker build.

#### Scenario: Loading demo content once
- **WHEN** `seed_loaddata` runs on an environment that has run `base_loaddata`
- **THEN** the sample artists and artworks referenced in `seed/` fixtures are created with taxonomy references resolving to the seeded base rows.

#### Scenario: Seed loading excluded from builds
- **WHEN** the Dockerfile or `start.sh` sets up an environment
- **THEN** only `base_loaddata` runs; `seed_loaddata` is not part of the build pipeline.

### Requirement: Fixture runner wired into environments
The system SHALL invoke `base_loaddata` after `migrate` in `start.sh` (the container runtime entrypoint, invoked by the Dockerfile CMD), and load base fixtures in tests where taxonomy rows are required. The Dockerfile build phase does not run `base_loaddata` because no database exists at build time.

#### Scenario: Every fresh environment is taxonomy-ready
- **WHEN** a new environment is built (Docker) or booted (start.sh)
- **THEN** the 36 taxonomy rows exist after `migrate` + `base_loaddata`.
