# Secure Catalog API — Delta Spec

## RENAMED Requirements

### Requirement: Public catalog endpoint
- FROM: ### Requirement: Public catalog endpoint
- TO: ### Requirement: Authenticated catalog endpoint

## MODIFIED Requirements

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

### Requirement: Catalog is stable for the frontend contract
The endpoint SHALL return consistent key names and value types across requests. Tests SHALL assert the full key contract, the available-only scoping, and the authentication requirement.

#### Scenario: Contract asserted by tests
- **WHEN** the test suite runs
- **THEN** tests SHALL assert the endpoint rejects anonymous requests, accepts a valid token, excludes non-buyable artworks, and returns every top-level key with the expected types.
