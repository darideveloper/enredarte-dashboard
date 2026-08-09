# Artist Admin Specification — Delta

## Purpose
Delta for the `artist-admin` capability: the Artist admin form/change view gains a location selector, the social links inline, and the readonly "Resumen" fieldset.

## ADDED Requirements

### Requirement: Location selector on Artist admin
The system SHALL add the `location` field to the `ArtistAdmin` edit form so an administrator can assign a shared `Location` to an artist.

#### Scenario: Assigning an artist location
- **WHEN** an administrator opens an Artist edit form
- **THEN** they can pick one `Location` for the artist (or leave it empty).

### Requirement: Social links inline on Artist admin
The system SHALL include the `ArtistSocialLinkInline` (`TabularInline`, sortable via `sort_order`) in the `ArtistAdmin` edit form.

#### Scenario: Editing social links with the artist
- **WHEN** an administrator opens an Artist edit form
- **THEN** they can add, remove, and reorder the artist's social links in place.

### Requirement: Changelist summary columns on Artist admin
The system SHALL add readonly count columns to the `ArtistAdmin` changelist for the derived blocks (artworks, available works, techniques, highlighted works, galleries), computed from the `Artist` derived properties (see `artist-derived-fields`).

#### Scenario: Viewing artist counts
- **WHEN** an administrator opens the Artist changelist
- **THEN** each row shows the computed counts for the derived blocks.

### Requirement: Readonly Resumen fieldset on Artist admin
The system SHALL render the derived profile blocks on the `ArtistAdmin` change form as a readonly "Resumen" fieldset in full detail, computed from the `Artist` derived properties (see `artist-derived-fields`).

#### Scenario: Viewing computed profile blocks
- **WHEN** an administrator opens an Artist edit form
- **THEN** the "Resumen" section displays the computed techniques, available works count, new additions, highlighted works, most viewed, and exhibiting galleries.
