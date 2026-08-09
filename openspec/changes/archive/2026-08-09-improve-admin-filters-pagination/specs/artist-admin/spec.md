# Artist Admin Delta

## ADDED Requirements

### Requirement: Artist location filter
The system SHALL add a `location` filter to the `ArtistAdmin` changelist so an administrator can browse artists by their assigned `Location`.

#### Scenario: Filtering artists by location
- **WHEN** an administrator opens the Artist changelist and selects a location in the "Ubicación" filter
- **THEN** only artists assigned to that location SHALL be shown.

#### Scenario: Location filter shows only in-use locations
- **WHEN** an administrator opens the Artist changelist and expands the "Ubicación" filter
- **THEN** only locations assigned to at least one artist SHALL be listed.

### Requirement: Artist created_at date filter
The system SHALL add `created_at` to the `ArtistAdmin` list filters so an administrator can filter artists by creation date range.

#### Scenario: Filtering recently onboarded artists
- **WHEN** an administrator opens the Artist changelist and applies a `created_at` date range
- **THEN** only artists created within that range SHALL be shown.

### Requirement: Artist has-artworks filter
The system SHALL add a "with/without artworks" filter to the `ArtistAdmin` changelist so an administrator can find artists with incomplete profiles (no artworks).

#### Scenario: Finding artists without artworks
- **WHEN** an administrator opens the Artist changelist and selects the "sin obras" lookup
- **THEN** only artists with no artworks SHALL be shown.

#### Scenario: Finding artists with artworks
- **WHEN** an administrator opens the Artist changelist and selects the "con obras" lookup
- **THEN** only artists with at least one artwork SHALL be shown.

### Requirement: Artist with-available-works filter
The system SHALL add a filter to the `ArtistAdmin` changelist that isolates artists currently having at least one active artwork with status `available`.

#### Scenario: Finding artists with sellable works
- **WHEN** an administrator opens the Artist changelist and selects the "con obras disponibles" lookup
- **THEN** only artists having at least one active `available` artwork SHALL be shown.

### Requirement: Artist changelist pagination
The system SHALL paginate the `ArtistAdmin` changelist at 50 rows per page.

#### Scenario: Browsing the Artist changelist
- **WHEN** an administrator opens the Artist changelist
- **THEN** at most 50 artists SHALL be rendered per page.
