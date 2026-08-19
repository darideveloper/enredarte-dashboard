## MODIFIED Requirements

### Requirement: Gallery endpoint
The system SHALL expose `GET /apis/artworks/galleries/` (list) and `GET /apis/artworks/galleries/{id}/` (detail). The queryset SHALL filter `is_active=True` and order by `-created_at`. Each entry SHALL include `id`, `slug`, `is_active`, `is_primary`, `created_at`, `updated_at`, `logo`, a `curator` reference as `{id, slug}` (or `null`), translations as `{es: {name, description}, en: {name, description}}`, and `artwork_links` as an array of `{id, artwork: {id, slug}, sort_order}`. Gallery entries SHALL NOT include a top-level `sort_order` field; `sort_order` SHALL remain on each `artwork_links` item.

#### Scenario: Gallery detail with artwork_links
- **WHEN** `GET /apis/artworks/galleries/1/` is requested
- **THEN** the response SHALL contain `translations` with `name` and `description` per language, `curator` as `{id, slug}` or `null`, and `artwork_links` as an array of `{id, artwork: {id, slug}, sort_order}`.

#### Scenario: Gallery logo returns absolute URL
- **WHEN** a gallery has a logo
- **THEN** the `logo` field SHALL be an absolute URL generated via `get_media_url()`.

#### Scenario: Gallery entry omits top-level sort_order
- **WHEN** a gallery is serialized
- **THEN** the response SHALL NOT contain a top-level `sort_order` key, while each `artwork_links` item SHALL still include it.

#### Scenario: Gallery entry includes is_primary
- **WHEN** a gallery is serialized
- **THEN** the response SHALL contain the `is_primary` boolean.
