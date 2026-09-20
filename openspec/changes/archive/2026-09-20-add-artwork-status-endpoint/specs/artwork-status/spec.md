## ADDED Requirements

### Requirement: Public artwork status endpoint
The system SHALL expose `GET /api/artworks/artworks/{slug}/status/` as a public endpoint (no authentication) that returns the live sale status and prices of a single artwork with no side effects.

#### Scenario: Available artwork returns live status and prices
- **WHEN** an anonymous `GET` hits `/api/artworks/artworks/{slug}/status/` for an active artwork with an active artist
- **THEN** the response SHALL be `200 OK` with body `{"slug": "<slug>", "status": "<enum>", "status_display": "<Spanish label>", "price_mxn": "<decimal string>", "price_usd": "<decimal string>", "updated_at": "<ISO-8601>"}` and no database write SHALL occur.

#### Scenario: Sold artwork reports sold
- **WHEN** an anonymous `GET` hits the status endpoint for an artwork with `status=sold`
- **THEN** the response SHALL be `200 OK` with `"status": "sold"` and `"status_display": "Vendida"`.

#### Scenario: Reserved artwork reports reserved
- **WHEN** an anonymous `GET` hits the status endpoint for an artwork with `status=reserved`
- **THEN** the response SHALL be `200 OK` with `"status": "reserved"`.

#### Scenario: Unknown slug returns 404
- **WHEN** a `GET` hits the status endpoint with a slug matching no artwork
- **THEN** the response SHALL be `404 Not Found` with body `{"status": "error", "message": "Not found.", "data": {}}`.

#### Scenario: Inactive artwork returns 404
- **WHEN** a `GET` hits the status endpoint for an artwork with `is_active=False` (or whose artist has `is_active=False`)
- **THEN** the response SHALL be `404 Not Found` with the same error body and no data SHALL be disclosed.

#### Scenario: Response is not cached
- **WHEN** the status endpoint returns `200 OK`
- **THEN** the response SHALL include a `Cache-Control: no-store` header.

### Requirement: Status endpoint throttling
The system SHALL rate-limit the status endpoint with a dedicated `artwork_status` `ScopedRateThrottle` scope at `120/hour` per client, so detail-page mounts stay well under budget while automated scraping is bounded.

#### Scenario: Throttle scope applied
- **WHEN** the `artwork_status` action handles a request
- **THEN** the view SHALL enforce the `artwork_status` throttle scope.

#### Scenario: Rate configured
- **WHEN** `REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]` is inspected
- **THEN** it SHALL contain `"artwork_status": "120/hour"`.

#### Scenario: Rate exceeded
- **WHEN** a client exceeds the `artwork_status` rate
- **THEN** the response SHALL be `429 Too Many Requests` and no artwork data SHALL be returned.

## Advisory: Frontend call contract (non-normative)

The following guidance targets the public frontend, which lives in a separate codebase. It is NOT enforced or tested by this backend; the requirements above fully define this change.

- The frontend should call the status endpoint once per artwork detail mount (no auth header), compare live `status` against the baked HTML, and swap the buy form for a `Vendida`/`Reservada` badge when they differ.
- The call should never block render; on any failure (network, `404`, `429`) the page should keep the baked HTML.
- `on_loan` and `not_available` should be treated like `sold` (badge, no buy form). Catalog cards are out of scope for this endpoint (no batch support in v1).
