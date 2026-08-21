# ArtCurator Admin Delta

## ADDED Requirements

### Requirement: ArtCurator has-galleries filter
The system SHALL add a "with/without galleries" filter to the `ArtCuratorAdmin` changelist so an administrator can identify curators who curate no galleries.

#### Scenario: Finding curators without galleries
- **WHEN** an administrator opens the ArtCurator changelist and selects the "sin galerías" lookup
- **THEN** only curators with no curated galleries SHALL be shown.

#### Scenario: Finding curators with galleries
- **WHEN** an administrator opens the ArtCurator changelist and selects the "con galerías" lookup
- **THEN** only curators curating at least one gallery SHALL be shown.
