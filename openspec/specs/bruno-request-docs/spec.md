# Bruno Request Docs Specification

## Purpose

To define the convention that every `.bru` request file in the Bruno collection SHALL carry a `docs` block documenting the expected API response (status codes and JSON shape). This applies to all 20 existing request files under `bruno/collections/enredarte-dashboard-api/` and is a mandatory requirement for any future endpoint added to the collection.

## Requirements

### Requirement: Every request file includes a docs block
Every `.bru` request file in `bruno/collections/enredarte-dashboard-api/` SHALL contain a `docs` block written in Markdown. The block SHALL be placed after the `headers` block and SHALL document at minimum: the endpoint purpose, the authentication requirement (`Authorization: Token`), the expected status codes, and the expected JSON response shape with a short JSON example derived from the implementation (`artworks/serializers.py`, `project/pagination.py`, `project/handlers.py`).

#### Scenario: Existing request file has docs block
- **WHEN** any of the 20 request files (`GET list.bru` or `GET detail.bru`) under `bruno/collections/enredarte-dashboard-api/<Model>/` is inspected
- **THEN** it SHALL contain a `docs { ... }` block that includes the endpoint purpose, the auth requirement, at least the `200` (and `401`) status codes, and a JSON example of the expected response.

#### Scenario: List request documents pagination envelope
- **WHEN** a `GET list.bru` file is inspected
- **THEN** its `docs` block SHALL document the paginated envelope (`count`, `next`, `previous`, `page`, `page_size`, `total_pages`, `results`) and include a list-item JSON example matching that resource's serializer.

#### Scenario: Detail request documents resource shape
- **WHEN** a `GET detail.bru` file is inspected
- **THEN** its `docs` block SHALL document the single-resource JSON shape matching that resource's serializer, plus the `404` status code with the project error envelope.

#### Scenario: Docs block is valid Bruno syntax
- **WHEN** a request file with a `docs` block is opened in the Bruno app
- **THEN** the request SHALL load without parse errors and the `docs` block SHALL render as Markdown in the Docs tab.

### Requirement: Error responses documented consistently
Every `docs` block SHALL document the project-wide error envelope `{status: "error", message, data}` for the error status codes it lists (at minimum `401`, and `404` for detail requests).

#### Scenario: 401 error documented
- **WHEN** a request file's `docs` block lists `401 Unauthorized`
- **THEN** it SHALL show the error envelope shape `{status, message, data}` matching `project/handlers.py`.

### Requirement: Future endpoints must include docs
Any API endpoint request file added to the Bruno collection after this change SHALL include a `docs` block following the same convention (purpose, auth, status codes, response shape with JSON example) as a condition of acceptance. The `docs/django-bruno.md` guide SHALL document this convention so contributors follow it.

#### Scenario: New endpoint documented by default
- **WHEN** a contributor adds a new `.bru` request file to the collection following `docs/django-bruno.md`
- **THEN** the guide SHALL instruct them to include a `docs` block with purpose, auth, status codes, and expected response shape, and the new file SHALL contain that `docs` block.

#### Scenario: Verification task checks for docs block
- **WHEN** the change's verification runs against the collection request files
- **THEN** it SHALL confirm every request file contains a `docs` block.