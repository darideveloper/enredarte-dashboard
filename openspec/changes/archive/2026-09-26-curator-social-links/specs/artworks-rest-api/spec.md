## MODIFIED Requirements

### Requirement: ArtCurator endpoint
The system SHALL expose `GET /api/artworks/art-curators/` (list) and `GET /api/artworks/art-curators/{id}/` (detail). The queryset SHALL filter `is_active=True` and order by `-created_at`. Each entry SHALL include `id`, `slug`, `is_active`, `created_at`, `updated_at`, `name`, `email`, `website`, `photo`, translations as `{es: {bio}, en: {bio}}`, and `social_links` as an array of `{id, platform, url}`. ArtCurator entries SHALL NOT include a `sort_order` field.

#### Scenario: ArtCurator detail response
- **WHEN** `GET /api/artworks/art-curators/1/` is requested
- **THEN** the response SHALL contain all curator fields, `translations` as `{es: {bio}, en: {bio}}`, and `social_links` as an array.

#### Scenario: ArtCurator without social links
- **WHEN** a curator has no social links
- **THEN** the `social_links` field SHALL be an empty array `[]`.

#### Scenario: ArtCurator photo returns absolute URL
- **WHEN** a curator has a photo
- **THEN** the `photo` field SHALL be an absolute URL generated via `get_media_url()`.

#### Scenario: ArtCurator entry omits sort_order
- **WHEN** a curator is serialized
- **THEN** the response SHALL NOT contain a `sort_order` key.
