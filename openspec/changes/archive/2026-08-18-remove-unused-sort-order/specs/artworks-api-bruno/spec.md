# Artworks API Bruno Collection — Delta

Delta spec for the `artworks-api-bruno` capability.

## MODIFIED Requirements

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