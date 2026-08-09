# Gallery Admin Delta

## ADDED Requirements

### Requirement: Gallery curator filter
The system SHALL add a `curator` filter to the `GalleryAdmin` changelist so an administrator can browse galleries by their assigned `ArtCurator`.

#### Scenario: Filtering galleries by curator
- **WHEN** an administrator opens the Gallery changelist and selects a curator in the "Curador" filter
- **THEN** only galleries curated by that curator SHALL be shown.

#### Scenario: Curator filter shows only in-use curators
- **WHEN** an administrator opens the Gallery changelist and expands the "Curador" filter
- **THEN** only curators curating at least one gallery SHALL be listed.

### Requirement: Gallery has-artworks filter
The system SHALL add a "with/without artworks" filter to the `GalleryAdmin` changelist so an administrator can identify galleries that are empty (no exhibited artworks).

#### Scenario: Finding empty galleries
- **WHEN** an administrator opens the Gallery changelist and selects the "sin obras" lookup
- **THEN** only galleries with no `ArtworkGallery` links SHALL be shown.

#### Scenario: Finding galleries with artworks
- **WHEN** an administrator opens the Gallery changelist and selects the "con obras" lookup
- **THEN** only galleries with at least one exhibited artwork SHALL be shown.
