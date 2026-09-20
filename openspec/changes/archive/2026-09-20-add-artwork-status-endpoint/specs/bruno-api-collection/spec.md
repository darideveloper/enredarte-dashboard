## ADDED Requirements

### Requirement: Artworks status request file
The collection SHALL contain an `Artworks/GET status.bru` request (seq 27) for `GET {{base_url}}/api/artworks/artworks/ciudad-reflejada/status/`. It SHALL carry no `Authorization` header (public endpoint) and SHALL contain a `docs` block per the `bruno-request-docs` convention stating the endpoint is public and throttled (`artwork_status 120/hour`), with status codes (`200`, `404`, `429`), the `200` response JSON (`slug`, `status`, `status_display`, `price_mxn`, `price_usd`, `updated_at`), and the `404`/`429` error shape. Its URL SHALL reference only `{{base_url}}` with the example slug `ciudad-reflejada` (same placeholder slug as `POST visit.bru`), and the `docs` block SHALL explain how to swap in a real slug.

#### Scenario: Status request exists in Artworks folder
- **WHEN** the collection is opened in Bruno
- **THEN** the `Artworks/` folder SHALL list `GET status` alongside `GET list`, `GET detail`, and `POST visit`.

#### Scenario: No auth header on status request
- **WHEN** the `GET status.bru` file is inspected
- **THEN** it SHALL NOT contain an `Authorization` header, its `get` block SHALL declare `auth: none`, and its `docs` block SHALL state the endpoint is public and throttled.

#### Scenario: No hardcoded hosts
- **WHEN** the `GET status.bru` file is inspected
- **THEN** its URL SHALL reference `{{base_url}}` and SHALL NOT hard-code hostnames or tokens.
