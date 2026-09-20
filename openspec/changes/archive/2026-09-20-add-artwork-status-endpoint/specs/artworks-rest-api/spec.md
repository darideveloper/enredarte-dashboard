## MODIFIED Requirements

### Requirement: All model endpoints require authentication
Every endpoint under `/api/artworks/` SHALL require authentication via the project's default DRF authentication classes (`TokenAuthentication` and `SessionAuthentication`). Unauthenticated requests SHALL receive `401 Unauthorized`. The artwork-sales endpoints (`POST artworks/{slug}/buy/`, `GET orders/{slug}/`, `POST orders/{slug}/delivery/`), the artwork view-tracking endpoint (`POST artworks/{slug}/visit/`), and the artwork-status endpoint (`GET artworks/{slug}/status/`) are the ONLY exceptions: they are intentionally public, protected by a scoped `ScopedRateThrottle` instead of authentication (order endpoints additionally by unguessable order slug tokens).

#### Scenario: Anonymous request rejected
- **WHEN** a request with no authentication credentials hits any `/api/artworks/` endpoint
- **THEN** the response SHALL be `401 Unauthorized`.

#### Scenario: Token-authenticated request succeeds
- **WHEN** a request with a valid `Authorization: Token <key>` header hits any `/api/artworks/` endpoint
- **THEN** the response SHALL be `200 OK` with the requested resource.

#### Scenario: Public sales endpoints exempted
- **WHEN** an anonymous request hits `POST artworks/{slug}/buy/`, `GET orders/{slug}/`, or `POST orders/{slug}/delivery/`
- **THEN** the request SHALL NOT receive `401`; it SHALL be processed by the artwork-sales public endpoint behavior (including throttling and validation).

#### Scenario: Public visit endpoint exempted
- **WHEN** an anonymous request hits `POST artworks/{slug}/visit/`
- **THEN** the request SHALL NOT receive `401`; it SHALL be processed by the artwork-view-tracking behavior (atomic increment, throttling, `404` for unknown/inactive slugs).

#### Scenario: Public status endpoint exempted
- **WHEN** an anonymous request hits `GET artworks/{slug}/status/`
- **THEN** the request SHALL NOT receive `401`; it SHALL be processed by the artwork-status behavior (side-effect-free read, throttling, `404` for unknown/inactive slugs or inactive artists).

#### Scenario: Read-only catalog endpoints stay authenticated
- **WHEN** an anonymous request hits a catalog endpoint such as `GET /api/artworks/artworks/`
- **THEN** the response SHALL remain `401 Unauthorized` (sales, view-tracking, and status endpoints do not weaken catalog auth).
