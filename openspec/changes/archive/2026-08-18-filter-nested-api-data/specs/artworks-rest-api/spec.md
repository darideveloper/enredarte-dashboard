# Artworks REST API Specification (Delta)

## MODIFIED Requirements

### Requirement: All querysets filter active rows
Every viewset queryset SHALL include `.filter(is_active=True)`. Inactive rows SHALL never
appear in any API response — including nested related objects. The Artwork queryset SHALL
additionally filter `artist__is_active=True`. Nested collections SHALL be filtered to active
rows (both through/link rows and targets, where the row carries an `is_active` field), and
single-FK refs (`Artist.location`, `Gallery.curator`) SHALL resolve to `null` when the
referenced row is inactive.

#### Scenario: Inactive taxonomy term excluded
- **WHEN** a Discipline has `is_active=False`
- **THEN** that discipline SHALL NOT appear in the disciplines list endpoint.

#### Scenario: Inactive nested rows excluded
- **WHEN** an active row references inactive related objects (gallery links, artwork links, images, social links, or taxonomy terms)
- **THEN** those inactive objects SHALL NOT appear in the API response.

#### Scenario: Inactive single-FK refs resolve to null
- **WHEN** an active Artist references an inactive Location or an active Gallery references an inactive ArtCurator
- **THEN** the corresponding ref field SHALL be `null`.

#### Scenario: Artwork of inactive artist excluded
- **WHEN** an active artwork references an Artist with `is_active=False`
- **THEN** the artwork SHALL NOT appear in the artworks list endpoint.