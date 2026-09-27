## Purpose

Defines the internal commission percentage field on the Artist model, establishing the commercial percentage split between the artist and Enredarte for artwork sales.

## ADDED Requirements

### Requirement: Artist commission storage and range validation
The system SHALL store an internal commission rate on the `Artist` model as an integer field (`commission`) representing the percentage (0 to 100) of artwork sales attributed to the artist. The field MUST enforce a minimum value of 0 and a maximum value of 100, default to 0 for existing and newly created records, and define admin-visible Spanish metadata (`verbose_name="Comisión del artista (%)"` and descriptive `help_text`).

#### Scenario: Valid commission rate within bounds
- **WHEN** an administrator creates or updates an `Artist` with a commission value between 0 and 100 inclusive
- **THEN** the value SHALL be saved successfully in the database.

#### Scenario: Commission rate below minimum rejected
- **WHEN** an artist record is validated with a commission value less than 0
- **THEN** validation SHALL fail with a validation error indicating the value must be greater than or equal to 0.

#### Scenario: Commission rate above maximum rejected
- **WHEN** an artist record is validated with a commission value greater than 100
- **THEN** validation SHALL fail with a validation error indicating the value must be less than or equal to 100.

#### Scenario: Default commission for artists
- **WHEN** a new `Artist` is instantiated without explicitly specifying a commission value
- **THEN** the `commission` field SHALL default to 0.

### Requirement: Internal commission remains excluded from public REST APIs
The system SHALL keep the artist commission field strictly internal to the database and Django Admin. The public REST API endpoints (`/api/artists/`, `/api/artworks/`) and their serializers MUST NOT expose the `commission` attribute in serialized responses.

#### Scenario: Querying public artist endpoints does not expose commission
- **WHEN** a client issues `GET /api/artists/artists/` or `GET /api/artists/artists/{slug}/`
- **THEN** the response payload SHALL NOT contain the `commission` field.

#### Scenario: Querying public artwork endpoints does not expose commission
- **WHEN** a client issues `GET /api/artworks/artworks/` or `GET /api/artworks/artworks/{slug}/`
- **THEN** the response payload and nested artist data SHALL NOT contain the `commission` field.
