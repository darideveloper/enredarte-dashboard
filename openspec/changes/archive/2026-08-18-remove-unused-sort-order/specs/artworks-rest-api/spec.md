# Artworks REST API — Delta

Delta spec for the `artworks-rest-api` capability.

## MODIFIED Requirements

### Requirement: Artist endpoint
The system SHALL expose `GET /apis/artworks/artists/` (list) and `GET /apis/artworks/artists/{id}/` (detail). The queryset SHALL filter `is_active=True` and order by `-created_at`. The list response SHALL be paginated. Each artist entry SHALL include all person fields (`id`, `slug`, `is_active`, `created_at`, `updated_at`, `name`, `email`, `website`, `photo`, `birth_year`, `death_year`), a `location` reference as `{id, slug}` (or `null`), translations as `{es: {bio}, en: {bio}}`, and `social_links` as an array of `{id, platform, url}`. Artist entries SHALL NOT include a `sort_order` field.

#### Scenario: Artist list is paginated
- **WHEN** `GET /apis/artworks/artists/` is requested
- **THEN** the response SHALL be a paginated envelope with `count`, `next`, `previous`, `page`, `page_size`, `total_pages`, and `results` containing artist objects ordered by `-created_at`.

#### Scenario: Artist detail with translations
- **WHEN** `GET /apis/artworks/artists/1/` is requested
- **THEN** the response SHALL contain all artist fields, `translations` as `{es: {bio}, en: {bio}}`, `social_links` as an array, and `location` as `{id, slug}` or `null`.

#### Scenario: Artist photo returns absolute URL
- **WHEN** an artist has a photo
- **THEN** the `photo` field SHALL be an absolute URL generated via `get_media_url()`.

#### Scenario: Artist without social links
- **WHEN** an artist has no social links
- **THEN** the `social_links` field SHALL be an empty array `[]`.

#### Scenario: Artist entry omits sort_order
- **WHEN** an artist is serialized
- **THEN** the response SHALL NOT contain a `sort_order` key.

#### Scenario: Inactive artists excluded
- **WHEN** an artist has `is_active=False`
- **THEN** that artist SHALL NOT appear in any artist endpoint response.

### Requirement: ArtCurator endpoint
The system SHALL expose `GET /apis/artworks/art-curators/` (list) and `GET /apis/artworks/art-curators/{id}/` (detail). The queryset SHALL filter `is_active=True` and order by `-created_at`. Each entry SHALL include `id`, `slug`, `is_active`, `created_at`, `updated_at`, `name`, `email`, `website`, `photo`, and translations as `{es: {bio}, en: {bio}}`. ArtCurator entries SHALL NOT include a `sort_order` field.

#### Scenario: ArtCurator detail response
- **WHEN** `GET /apis/artworks/art-curators/1/` is requested
- **THEN** the response SHALL contain all curator fields and `translations` as `{es: {bio}, en: {bio}}`.

#### Scenario: ArtCurator photo returns absolute URL
- **WHEN** a curator has a photo
- **THEN** the `photo` field SHALL be an absolute URL generated via `get_media_url()`.

#### Scenario: ArtCurator entry omits sort_order
- **WHEN** a curator is serialized
- **THEN** the response SHALL NOT contain a `sort_order` key.

### Requirement: Location endpoint
The system SHALL expose `GET /apis/artworks/locations/` (list) and `GET /apis/artworks/locations/{id}/` (detail). The queryset SHALL filter `is_active=True` and order by `-created_at`. Each entry SHALL include `id`, `slug`, `is_active`, `created_at`, `updated_at`, and translations as `{es: {name}, en: {name}}`. Location entries SHALL NOT include a `sort_order` field.

#### Scenario: Location list response
- **WHEN** `GET /apis/artworks/locations/` is requested
- **THEN** the response SHALL be a paginated list of location objects with `translations` as `{es: {name}, en: {name}}`.

#### Scenario: Location entry omits sort_order
- **WHEN** a location is serialized
- **THEN** the response SHALL NOT contain a `sort_order` key.

### Requirement: Gallery endpoint
The system SHALL expose `GET /apis/artworks/galleries/` (list) and `GET /apis/artworks/galleries/{id}/` (detail). The queryset SHALL filter `is_active=True` and order by `-created_at`. Each entry SHALL include `id`, `slug`, `is_active`, `created_at`, `updated_at`, `logo`, a `curator` reference as `{id, slug}` (or `null`), translations as `{es: {name, description}, en: {name, description}}`, and `artwork_links` as an array of `{id, artwork: {id, slug}, sort_order}`. Gallery entries SHALL NOT include a top-level `sort_order` field; `sort_order` SHALL remain on each `artwork_links` item.

#### Scenario: Gallery detail with artwork_links
- **WHEN** `GET /apis/artworks/galleries/1/` is requested
- **THEN** the response SHALL contain `translations` with `name` and `description` per language, `curator` as `{id, slug}` or `null`, and `artwork_links` as an array of `{id, artwork: {id, slug}, sort_order}`.

#### Scenario: Gallery logo returns absolute URL
- **WHEN** a gallery has a logo
- **THEN** the `logo` field SHALL be an absolute URL generated via `get_media_url()`.

#### Scenario: Gallery entry omits top-level sort_order
- **WHEN** a gallery is serialized
- **THEN** the response SHALL NOT contain a top-level `sort_order` key, while each `artwork_links` item SHALL still include it.

### Requirement: Taxonomy endpoints (Discipline, Technique, Theme, Format, Scale)
The system SHALL expose list and detail endpoints for each taxonomy model: `Discipline` at `/apis/artworks/disciplines/`, `Technique` at `/apis/artworks/techniques/`, `Theme` at `/apis/artworks/themes/`, `Format` at `/apis/artworks/formats/`, and `Scale` at `/apis/artworks/scales/`. All SHALL filter `is_active=True`, order by `-created_at`, and include `id`, `slug`, `is_active`, `created_at`, `updated_at`, and translations as `{es: {name}, en: {name}}`. Taxonomy entries SHALL NOT include a `sort_order` field.

#### Scenario: Discipline list paginated
- **WHEN** `GET /apis/artworks/disciplines/` is requested
- **THEN** the response SHALL be a paginated list of discipline objects with `translations` containing `name` per language.

#### Scenario: Taxonomy detail consistent across all five
- **WHEN** `GET /apis/artworks/formats/1/` is requested
- **THEN** the response SHALL contain `id`, `slug`, `is_active`, `created_at`, `updated_at`, and `translations` as `{es: {name}, en: {name}}`.

#### Scenario: Taxonomy entry omits sort_order
- **WHEN** any taxonomy term is serialized
- **THEN** the response SHALL NOT contain a `sort_order` key.

### Requirement: Artwork endpoint
The system SHALL expose `GET /apis/artworks/artworks/` (list) and `GET /apis/artworks/artworks/{id}/` (detail). The queryset SHALL filter `is_active=True` and order by `-created_at`. Each entry SHALL include `id`, `slug`, `is_active`, `created_at`, `updated_at`, `artist` as `{id, slug}`, `year`, `dimensions`, `disciplines`, `techniques`, `themes`, `formats`, `scales` each as an array of `{id, slug}` objects, `price_mxn` and `price_usd` as numbers, `status` as its raw choice value, `is_highlighted`, `views_count`, translations as `{es: {title, description}, en: {title, description}}`, `images` as an array of `{id, image, alt_es, alt_en, is_primary, sort_order}`, and `gallery_links` as an array of `{id, gallery: {id, slug}, sort_order}`. Artwork entries SHALL NOT include a top-level `sort_order` field; `sort_order` SHALL remain on each `images` and `gallery_links` item.

#### Scenario: Artwork list paginated
- **WHEN** `GET /apis/artworks/artworks/` is requested
- **THEN** the response SHALL be a paginated list of artwork objects with all fields described above, ordered by `-created_at`.

#### Scenario: Artwork detail with nested images
- **WHEN** `GET /apis/artworks/artworks/1/` is requested
- **THEN** the response SHALL contain `images` as an array where each image has `image` as an absolute URL, `alt_es`, `alt_en`, `is_primary`, and `sort_order`.

#### Scenario: Artwork M2M references as objects
- **WHEN** an artwork belongs to taxonomy groups
- **THEN** each M2M field (`disciplines`, `techniques`, `themes`, `formats`, `scales`) SHALL be an array of `{id, slug}` objects, empty when the artwork has none.

#### Scenario: Artwork detail with gallery links
- **WHEN** `GET /apis/artworks/artworks/1/` is requested
- **THEN** `gallery_links` SHALL be an array of `{id, gallery: {id, slug}, sort_order}`, empty when the artwork has no gallery links.

#### Scenario: Artwork entry omits top-level sort_order
- **WHEN** an artwork is serialized
- **THEN** the response SHALL NOT contain a top-level `sort_order` key, while each `images` and `gallery_links` item SHALL still include it.