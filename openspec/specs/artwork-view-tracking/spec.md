# Artwork View Tracking Specification

## Purpose
To define the public endpoint that records real artwork detail views from the frontend — atomically incrementing `Artwork.views_count` behind the artist profile's "Más visitados" block — including its throttling and the non-normative frontend call guidance.

## Requirements

### Requirement: Public visit increment endpoint
The system SHALL expose `POST /api/artworks/artworks/{slug}/visit/` as a public endpoint (no authentication) that atomically increments the artwork's `views_count` by exactly 1 and returns the new count. The endpoint takes no input; any request body SHALL be ignored.

#### Scenario: First visit increments from zero
- **WHEN** an anonymous `POST` hits `/api/artworks/artworks/{slug}/visit/` for an active artwork with `views_count = 0`
- **THEN** the response SHALL be `200 OK` with body `{"views_count": 1}` and the stored counter SHALL be `1`.

#### Scenario: Repeat visits accumulate raw
- **WHEN** two consecutive anonymous `POST`s hit the visit endpoint for the same artwork
- **THEN** each SHALL return `200 OK` and the counter SHALL increase by 1 per call (no dedup).

#### Scenario: Request body is ignored
- **WHEN** a `POST` includes an arbitrary body
- **THEN** the counter SHALL still increment by exactly 1 and the response SHALL be `200 OK` with the new count.

#### Scenario: Unknown slug returns 404 without side effects
- **WHEN** a `POST` hits the visit endpoint with a slug matching no artwork
- **THEN** the response SHALL be `404 Not Found` and no counter SHALL change.

#### Scenario: Inactive artwork returns 404 without side effects
- **WHEN** a `POST` hits the visit endpoint for an artwork with `is_active=False` (or whose artist is inactive)
- **THEN** the response SHALL be `404 Not Found` and the counter SHALL NOT change.

### Requirement: Visit endpoint throttling
The system SHALL rate-limit the visit endpoint with a dedicated `artwork_views` `ScopedRateThrottle` scope so automated traffic cannot inflate counters unbounded.

#### Scenario: Throttle scope applied
- **WHEN** the `visit` action handles a request
- **THEN** the view SHALL enforce the `artwork_views` throttle scope.

#### Scenario: Rate exceeded
- **WHEN** a client exceeds the `artwork_views` rate
- **THEN** the response SHALL be `429 Too Many Requests` and the counter SHALL NOT change.

## Advisory: Frontend call contract (non-normative)

The following guidance targets the public frontend, which lives in a separate codebase. It is NOT enforced or tested by this backend; the requirements above fully define this change.

- The frontend should call the visit endpoint exactly once per artwork detail mount as a fire-and-forget `POST` with no auth header, and may display the returned `views_count`.
- The call should never block render and never retry on failure; if the `POST` fails (network, `429`, `404`), the page should still render with the previously loaded data.
