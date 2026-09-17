# artworks-rest-api Delta Spec

## MODIFIED Requirements

### Requirement: All model endpoints require authentication
Every endpoint under `/api/artworks/` SHALL require authentication via the project's default DRF authentication classes (`TokenAuthentication` and `SessionAuthentication`). Unauthenticated requests SHALL receive `401 Unauthorized`. The artwork-sales endpoints introduced by the `artwork-sales` capability (`POST artworks/{slug}/buy/`, `GET orders/{slug}/`, `POST orders/{slug}/delivery/`) are the ONLY exceptions: they are intentionally public, protected by unguessable order slug tokens and a scoped `AnonRateThrottle` instead of authentication.

#### Scenario: Anonymous request rejected
- **WHEN** a request with no authentication credentials hits any `/api/artworks/` endpoint
- **THEN** the response SHALL be `401 Unauthorized`.

#### Scenario: Token-authenticated request succeeds
- **WHEN** a request with a valid `Authorization: Token <key>` header hits any `/api/artworks/` endpoint
- **THEN** the response SHALL be `200 OK` with the requested resource.

#### Scenario: Public sales endpoints exempted
- **WHEN** an anonymous request hits `POST artworks/{slug}/buy/`, `GET orders/{slug}/`, or `POST orders/{slug}/delivery/`
- **THEN** the request SHALL NOT receive `401`; it SHALL be processed by the artwork-sales public endpoint behavior (including throttling and validation).

#### Scenario: Read-only catalog endpoints stay authenticated
- **WHEN** an anonymous request hits a catalog endpoint such as `GET /api/artworks/artworks/`
- **THEN** the response SHALL remain `401 Unauthorized` (sales endpoints do not weaken catalog auth).
