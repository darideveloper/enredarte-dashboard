# Artwork Admin Specification — Delta

## Purpose
Delta for the `artwork-admin` capability: the Artwork admin form, changelist, and filters gain the `is_highlighted` and `views_count` discovery fields.

## ADDED Requirements

### Requirement: Discovery fields in the artwork form
The system SHALL add `is_highlighted` and `views_count` to the `ArtworkAdmin` edit form so an administrator can toggle featured status and set the views counter manually.

#### Scenario: Editing discovery fields
- **WHEN** an administrator opens an Artwork edit form
- **THEN** they can check `is_highlighted` and enter a `views_count` value.

### Requirement: Discovery fields in the artwork changelist and filters
The system SHALL display `is_highlighted` and `views_count` as columns in the `ArtworkAdmin` changelist and SHALL add `is_highlighted` as a list filter.

#### Scenario: Viewing and filtering discovery fields
- **WHEN** an administrator opens the Artwork changelist
- **THEN** they see highlighted state and views count per row and can filter by `is_highlighted`.
