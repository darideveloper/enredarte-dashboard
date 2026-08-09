# Artist Derived Fields Specification

## Purpose
To define the reusable computed properties on `Artist` — techniques, available works, new additions, highlighted works, most viewed, and curations — and the readonly admin "Resumen" fieldset that renders them. These properties are the single source of truth consumed by both the admin and the future DRF API.

## ADDED Requirements

### Requirement: Derived techniques property
The system SHALL provide `Artist.techniques` returning the distinct `Technique` queryset across the artist's artworks, so the profile's "Técnicas" block is auto-calculated.

#### Scenario: Techniques come from artworks
- **WHEN** an artist's artworks use several techniques
- **THEN** `artist.techniques` returns each distinct technique, with no duplicates.

### Requirement: Derived available works property
The system SHALL provide `Artist.available_artworks` returning the artist's active artworks with status `available`, so the "Obras disponibles" block is auto-calculated.

#### Scenario: Filtering available works
- **WHEN** an artist has available, sold, and reserved artworks
- **THEN** `artist.available_artworks` only contains the active artworks whose status is `available`.

### Requirement: Derived new additions property
The system SHALL provide `Artist.new_additions` returning the artist's active artworks ordered by `created_at` descending, so the "Nuevas incorporaciones" block is auto-calculated.

#### Scenario: Newest works first
- **WHEN** an artist has artworks added at different times
- **THEN** `artist.new_additions` lists them newest first.

### Requirement: Derived highlighted works property
The system SHALL provide `Artist.highlighted_artworks` returning the artist's active artworks with `is_highlighted=True`, so the "Destacados" block is auto-calculated.

#### Scenario: Featured works only
- **WHEN** an artist has some highlighted and some non-highlighted artworks
- **THEN** `artist.highlighted_artworks` only contains the active, highlighted ones.

### Requirement: Derived most viewed property
The system SHALL provide `Artist.most_viewed` returning the artist's active artworks ordered by `views_count` descending, so the "Más visitados" block is auto-calculated.

#### Scenario: Most visited first
- **WHEN** an artist's artworks have different `views_count` values
- **THEN** `artist.most_viewed` lists them from most to least viewed.

### Requirement: Derived curations property
The system SHALL provide `Artist.curations` returning the distinct active `Gallery` objects exhibiting the artist's works (via `ArtworkGallery`), so the "Curadurías" block is auto-calculated.

#### Scenario: Galleries exhibiting the artist
- **WHEN** some of the artist's artworks are linked to galleries
- **THEN** `artist.curations` returns each exhibiting gallery once, even when several of the artist's works are in the same gallery.

### Requirement: Reusable calculation source
The system SHALL implement all derived blocks as model properties on `Artist` returning QuerySets, so the admin and future DRF serializers consume the same computation without duplication. Admin rendering (counts vs. lists) SHALL be presentation-only and never alter the underlying queryset.

#### Scenario: Admin and API share the source
- **WHEN** a future DRF serializer exposes an artist block
- **THEN** it can call the same `Artist` property the admin uses, receiving the raw QuerySet.

#### Scenario: Different admin views, same data
- **WHEN** the artist changelist shows a block as a count and the artist change form shows the same block as a full list
- **THEN** both derive from the same `Artist` property (`.count()` vs. `.all()`), with no duplicated computation.

### Requirement: Admin changelist summary columns
The system SHALL add readonly count columns to `ArtistAdmin`'s changelist for the derived blocks — number of artworks, available works, techniques, highlighted works, and exhibiting galleries.

#### Scenario: Viewing artist counts in the list
- **WHEN** an administrator opens the Artist changelist
- **THEN** each row shows the computed counts (artworks, available, techniques, highlighted, galleries).

### Requirement: Admin readonly Resumen fieldset
The system SHALL add a readonly "Resumen" fieldset on `ArtistAdmin`'s change form that renders the derived blocks in detail — techniques names, available works count, new additions list, highlighted works, most viewed, and exhibiting galleries — via admin `display_*` methods over the model properties.

#### Scenario: Viewing the artist summary
- **WHEN** an administrator opens an Artist edit form
- **THEN** a "Resumen" section shows the computed techniques, available works count, new additions, highlighted works, most viewed, and exhibiting galleries.
