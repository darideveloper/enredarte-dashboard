# Artworks API Bruno Collection Specification (Delta)

## Purpose

This delta spec captures the update of the 20 Bruno request files in the collection to include a `docs` block documenting the expected API response, following the new `bruno-request-docs` convention.

## MODIFIED Requirements

### Requirement: List requests target paginated list endpoints
Each `GET list.bru` SHALL send `GET {{base_url}}/apis/artworks/<resource>/` with header `Authorization: Token {{token}}`. The `meta` block SHALL set `type: http` and assign a sequential `seq` number. Each `GET list.bru` SHALL also contain a `docs` block documenting the endpoint purpose, the auth requirement, the `200` and `401` status codes, and the paginated response envelope with a list-item JSON example matching the resource's serializer.

#### Scenario: Artists list request
- **WHEN** `GET list.bru` in the `Artists/` folder is inspected
- **THEN** its URL SHALL be `{{base_url}}/apis/artworks/artists/`, it SHALL include the `Authorization: Token {{token}}` header, and it SHALL contain a `docs` block with the paginated envelope and an artist JSON example.

#### Scenario: Artwork list request documents nested shapes
- **WHEN** `GET list.bru` in the `Artworks/` folder is inspected
- **THEN** its `docs` block SHALL document the artwork list-item shape including `artist` as `{id, slug}`, taxonomy arrays of `{id, slug}`, `price_mxn`/`price_usd` as numbers, `translations`, `images`, and `gallery_links`.

### Requirement: Detail requests target single resource
Each `GET detail.bru` SHALL send `GET {{base_url}}/apis/artworks/<resource>/1/` with header `Authorization: Token {{token}}`, using a hardcoded ID of `1` as a placeholder the developer can change. Each `GET detail.bru` SHALL also contain a `docs` block documenting the endpoint purpose, the `200`, `401`, and `404` status codes, the single-resource JSON shape matching the resource's serializer, and the project error envelope for error responses.

#### Scenario: Artwork detail request
- **WHEN** `GET detail.bru` in the `Artworks/` folder is inspected
- **THEN** its URL SHALL be `{{base_url}}/apis/artworks/artworks/1/`, it SHALL include the `Authorization: Token {{token}}` header, and it SHALL contain a `docs` block with the artwork JSON shape, the `404` status code, and the `{status, message, data}` error envelope.

#### Scenario: Taxonomy detail request
- **WHEN** `GET detail.bru` in the `Disciplines/` folder is inspected
- **THEN** its `docs` block SHALL document the taxonomy resource shape (`id`, `slug`, `is_active`, `sort_order`, `created_at`, `updated_at`, `translations` as `{es: {name}, en: {name}}`).
