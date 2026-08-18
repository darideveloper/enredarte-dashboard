# Artworks API Bruno Collection Specification

## Purpose

This specification defines a Bruno API collection for all 10 model endpoints exposed by the `artworks-rest-api` spec. It replaces the legacy `bruno-api-collection` which only covered `GET /api/catalog/` and `GET /api/`.

## Requirements

### Requirement: Per-model request folders
The system SHALL organize 20 Bruno request files into 10 folders, one per model: `Artists/`, `ArtCurators/`, `Locations/`, `Galleries/`, `Disciplines/`, `Techniques/`, `Themes/`, `Formats/`, `Scales/`, `Artworks/`. Each folder SHALL contain exactly two files: `GET list.bru` and `GET detail.bru`.

#### Scenario: Each model has two request files
- **WHEN** the `bruno/collections/enredarte-dashboard-api/` directory is inspected
- **THEN** it SHALL contain 10 subdirectories, each with `GET list.bru` and `GET detail.bru`.

### Requirement: List requests target paginated list endpoints
Each `GET list.bru` SHALL send `GET {{base_url}}/apis/artworks/<resource>/` with header `Authorization: Token {{token}}`. The `meta` block SHALL set `type: http` and assign a sequential `seq` number. Each `GET list.bru` SHALL also contain a `docs` block documenting the endpoint purpose, the auth requirement, the `200` and `401` status codes, and the paginated response envelope with a list-item JSON example matching the resource's serializer.

#### Scenario: Artists list request
- **WHEN** `GET list.bru` in the `Artists/` folder is inspected
- **THEN** its URL SHALL be `{{base_url}}/apis/artworks/artists/`, it SHALL include the `Authorization: Token {{token}}` header, and it SHALL contain a `docs` block with the paginated envelope and an artist JSON example.

#### Scenario: Artwork list request documents nested shapes
- **WHEN** `GET list.bru` in the `Artworks/` folder is inspected
- **THEN** its `docs` block SHALL document the artwork list-item shape including `artist` as `{id, slug}`, taxonomy arrays of `{id, slug}`, `price_mxn`/`price_usd` as numbers, `translations`, `images`, and `gallery_links`.

### Requirement: Detail requests target single resource
Each `GET detail.bru` SHALL send `GET {{base_url}}/apis/artworks/<resource>/1/` with header `Authorization: Token {{token}}`, using a hardcoded ID of `1` as a placeholder the developer can change. Each `GET detail.bru` SHALL also contain a `docs` block documenting the endpoint purpose, the `200`, `401`, and `404` status codes, the single-resource JSON shape matching the resource's serializer, and the project error envelope for error responses. The documented shapes SHALL omit `sort_order` for all top-level resources.

#### Scenario: Artwork detail request
- **WHEN** `GET detail.bru` in the `Artworks/` folder is inspected
- **THEN** its URL SHALL be `{{base_url}}/apis/artworks/artworks/1/`, it SHALL include the `Authorization: Token {{token}}` header, and it SHALL contain a `docs` block with the artwork JSON shape, the `404` status code, and the `{status, message, data}` error envelope.

#### Scenario: Taxonomy detail request
- **WHEN** `GET detail.bru` in the `Disciplines/` folder is inspected
- **THEN** its `docs` block SHALL document the taxonomy resource shape (`id`, `slug`, `is_active`, `created_at`, `updated_at`, `translations` as `{es: {name}, en: {name}}`) without `sort_order`.

#### Scenario: Nested sort_order preserved in examples
- **WHEN** a `docs` block documents artwork or gallery detail
- **THEN** `images`, `gallery_links`, and `artwork_links` items SHALL still include `sort_order`.

### Requirement: Environment file preserved and reused
The existing `bruno/collections/enredarte-dashboard-api/environments/dev.bru` SHALL be preserved with its `base_url` and `token` variables. The tracked `dev.bru.example` template SHALL also remain unchanged. No new environment files SHALL be created. All 20 new request files SHALL reference `{{base_url}}` and `{{token}}`.

#### Scenario: Dev environment unchanged
- **WHEN** the change is applied
- **THEN** `environments/dev.bru` SHALL contain the same `base_url` and `token` variables it had before the change, and `environments/dev.bru.example` SHALL remain the committed placeholder template.

### Requirement: Workspace and collection metadata preserved
The existing `bruno/workspace.yml` and `bruno/collections/enredarte-dashboard-api/bruno.json` SHALL be preserved. Their content SHALL NOT change.

#### Scenario: Workspace structure maintained
- **WHEN** the Bruno workspace is opened after the change
- **THEN** the workspace SHALL load successfully with all 20 request files visible in the Bruno app.

### Requirement: README updated to reflect new endpoints
The `bruno/README.md` SHALL be updated to document the new endpoint structure. It SHALL explain that the API now has 10 model-specific endpoints under `/apis/artworks/` instead of a single catalog endpoint, and SHALL describe how to use the per-model request files.

#### Scenario: README explains new structure
- **WHEN** a developer reads `bruno/README.md`
- **THEN** it SHALL describe the 10 model endpoints and explain how to use the Bruno request files to test them.
