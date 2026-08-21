## ADDED Requirements

### Requirement: Artist admin form field ordering
The system SHALL organize the `ArtistAdmin` form using `fieldsets` to logically group fields and ensure `slug` directly follows `name`.

#### Scenario: Creating or editing an artist
- **WHEN** an administrator views the Artist add or edit form
- **THEN** fields SHALL be organized into logical sections (e.g., Personal Info, Contact & Media, System Status) with the `slug` field positioned immediately after `name` to visually support auto-population.
