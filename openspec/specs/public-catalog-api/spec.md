# Public Catalog API Specification

## Purpose
To define the authenticated, read-only `GET /api/catalog/` endpoint that returns the entire buyable catalogue in a single, unpaginated fetch requiring an authenticated user — artworks (`is_active=True`, `status="available"`), artists, taxonomy groups (disciplines, techniques, themes, formats, scales), and locations, denormalized and bilingual (es/en) so the frontend static build can render both locale routes from one payload. The DRF `Token` acts as the API key for the frontend static build.

## Requirements

### Requirement: Authenticated catalog endpoint
The system SHALL expose a read-only endpoint `GET /api/catalog/` that returns the entire buyable catalogue in a single response, **requiring authentication** and without pagination. The endpoint SHALL use the global default dual authentication (`TokenAuthentication` and `SessionAuthentication`) and SHALL require an authenticated user (`IsAuthenticated`). The DRF `Token` acts as the API key for the SSG build.

#### Scenario: Anonymous request rejected
- **WHEN** a request with no authentication credentials hits `GET /api/catalog/`
- **THEN** the response SHALL be `401 Unauthorized`.

#### Scenario: Token-authenticated request succeeds
- **WHEN** a request with a valid `Authorization: Token <key>` header hits `GET /api/catalog/`
- **THEN** the response SHALL be `200 OK` with the full catalog payload.

#### Scenario: Session-authenticated request succeeds
- **WHEN** a logged-in user's session requests `GET /api/catalog/`
- **THEN** the response SHALL be `200 OK` with the full catalog payload.

#### Scenario: Response is not paginated
- **WHEN** the catalog endpoint is requested
- **THEN** the response body SHALL be the raw catalog object (not a paginated `{results, count, ...}` envelope) and SHALL contain every matching artwork.

### Requirement: Catalog only includes buyable artworks
The catalog SHALL include only artworks with `is_active=True` and `status="available"`. Artworks that are sold, reserved, on loan, not available, or inactive SHALL be excluded.

#### Scenario: Sold artwork excluded
- **WHEN** a catalog contains an artwork with `status="sold"`
- **THEN** that artwork SHALL NOT appear anywhere in the catalog response.

#### Scenario: Inactive artwork excluded
- **WHEN** a catalog contains an artwork with `is_active=False`
- **THEN** that artwork SHALL NOT appear in the catalog response.

#### Scenario: Available artwork included
- **WHEN** a catalog contains an artwork with `is_active=True` and `status="available"`
- **THEN** that artwork SHALL appear in the `artworks` array.

### Requirement: Catalog response structure
The catalog response SHALL contain, at the top level: `generated_at`, `artists` (list), `taxonomies` (object with `disciplines`, `techniques`, `themes`, `formats`, `scales` lists), `locations` (list), and `artworks` (list). Taxonomy lists SHALL be present even when empty.

#### Scenario: All top-level keys present
- **WHEN** `GET /api/catalog/` is requested
- **THEN** the response object SHALL contain keys `generated_at`, `artists`, `taxonomies`, `locations`, and `artworks`.

#### Scenario: All taxonomy groups present
- **WHEN** a catalog contains no artworks of a given taxonomy group
- **THEN** that group SHALL still be present in the `taxonomies` object as an empty list.

### Requirement: Category reference entries carry both languages
Each artist, taxonomy, and location entry SHALL carry `id`, `slug`, an `es` name and an `en` name. Artist entries SHALL additionally carry `location_id`. Taxonomy lists SHALL be ordered by `sort_order`.

#### Scenario: Bilingual names returned
- **WHEN** an artist, taxonomy term, or location has both Spanish and English translations
- **THEN** the response entry SHALL contain the Spanish name in a `name_es` field and the English name in a `name_en` field.

#### Scenario: Missing translation falls back
- **WHEN** a taxonomy term or location exists in only one language
- **THEN** the missing-language name SHALL fall back to the available one (or the slug when no translation exists), matching the frontend display conventions.

#### Scenario: Artist name is language-independent
- **WHEN** an artist entry is serialized
- **THEN** both `name_es` and `name_en` SHALL be the artist's `Person.name`, since artists have no per-language name translation.

#### Scenario: Ordered by sort_order
- **WHEN** a taxonomy list is returned
- **THEN** entries SHALL be ordered by the taxonomy model's `sort_order`.

#### Scenario: Locations list mirrors taxonomy entries
- **WHEN** an artwork's artist has a `location`
- **THEN** that location SHALL appear in the top-level `locations` list with `id`, `slug`, `name_es`, `name_en`, and the artist entry SHALL reference it via `location_id`. Artists without a location SHALL have `location_id` null.

### Requirement: Artwork entries are denormalized for faceting
Each artwork entry SHALL contain: `id`, `slug`, `title_es`, `title_en`, `image` (primary artwork image URL or null), `image_alt_es`, `image_alt_en`, `artist_id`, `year`, `dimensions`, `price_mxn`, `price_usd`, and the five id arrays `disciplines`, `techniques`, `themes`, `formats`, `scales`. `price_mxn`/`price_usd` SHALL be JSON numbers, and `generated_at` SHALL be an ISO-8601 UTC timestamp ending in `Z`.

#### Scenario: Primary image selected first
- **WHEN** an artwork has an image flagged `is_primary=True`
- **THEN** the entry's `image` SHALL be that image's URL.

#### Scenario: Fallback image when no primary
- **WHEN** an artwork has no primary-flagged image
- **THEN** the entry's `image` SHALL be the URL of the first image ordered by `sort_order`, or `null` when the artwork has no images.

#### Scenario: Bilingual alt text returned
- **WHEN** an artwork entry is serialized
- **THEN** `image_alt_es` SHALL be the selected image's `alt_es` and `image_alt_en` SHALL be its `alt_en`, each falling back to the corresponding translated title when the alt field is empty.

#### Scenario: Taxonomy ids returned as arrays
- **WHEN** an artwork belongs to a taxonomy group
- **THEN** the corresponding key (`disciplines`, `techniques`, `themes`, `formats`, `scales`) SHALL be an array of taxonomy ids, empty when the artwork has none.

### Requirement: Catalog is stable for the frontend contract
The endpoint SHALL return consistent key names and value types across requests. Tests SHALL assert the full key contract, the available-only scoping, and the authentication requirement.

#### Scenario: Contract asserted by tests
- **WHEN** the test suite runs
- **THEN** tests SHALL assert the endpoint rejects anonymous requests, accepts a valid token, excludes non-buyable artworks, and returns every top-level key with the expected types.
