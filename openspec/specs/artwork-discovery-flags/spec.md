# Artwork Discovery Flags Specification

## Purpose
To define the `Artwork` fields that back the artist profile's "Destacados" and "Más visitados" blocks — `is_highlighted` and `views_count` — and their admin exposure.

## Requirements

### Requirement: Highlighted flag on Artwork
The system SHALL add `Artwork.is_highlighted` (`BooleanField`, default `False`) so artworks can be globally marked as featured and each artist's profile can filter its own featured works.

#### Scenario: Marking an artwork as highlighted
- **WHEN** an administrator checks `is_highlighted` on an artwork
- **THEN** the artwork is marked featured and appears in its artist's highlighted works.

#### Scenario: Default not highlighted
- **WHEN** an artwork is created without touching the flag
- **THEN** `is_highlighted` is `False`.

### Requirement: Views counter on Artwork
The system SHALL add `Artwork.views_count` (`PositiveIntegerField`, default `0`) as the field that a future public API/view will increment; while no view exists, it SHALL be editable in the admin so values can be set manually.

#### Scenario: Tracking views
- **WHEN** a public artwork detail view (added later) is visited
- **THEN** it can increment the artwork's `views_count`; the artist's "most viewed" block orders works by this field descending.

#### Scenario: Manual counter seeding
- **WHEN** an administrator edits an artwork
- **THEN** they can set `views_count` directly.

### Requirement: Discovery flags admin exposure
The system SHALL expose `is_highlighted` and `views_count` on `ArtworkAdmin` in the edit form, the changelist columns, and the list filters (`is_highlighted` as a filter).

#### Scenario: Managing flags in the artwork form
- **WHEN** an administrator opens an Artwork edit form
- **THEN** they can toggle `is_highlighted` and set `views_count`.

#### Scenario: Filtering highlighted artworks
- **WHEN** an administrator opens the Artwork changelist
- **THEN** they can filter by `is_highlighted` and see both fields as columns.
