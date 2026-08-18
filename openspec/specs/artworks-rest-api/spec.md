# Artworks REST API Specification

## Purpose

This specification defines 10 read-only, paginated, authenticated API endpoints under `/apis/artworks/` — one per domain model in the `artworks` app — replacing the legacy monolithic `GET /api/catalog/`.

All endpoints follow REST conventions: list returns a paginated envelope, detail returns a single resource. Translations are nested as `{language: {field: value}}` dicts, related models are referenced via `{id, slug}` objects, and sub-objects (social links, images, gallery links) are inlined.

## Requirements

### Requirement: All model endpoints require authentication
Every endpoint under `/apis/artworks/` SHALL require authentication via the project's default DRF authentication classes (`TokenAuthentication` and `SessionAuthentication`). Unauthenticated requests SHALL receive `401 Unauthorized`.

#### Scenario: Anonymous request rejected
- **WHEN** a request with no authentication credentials hits any `/apis/artworks/` endpoint
- **THEN** the response SHALL be `401 Unauthorized`.

#### Scenario: Token-authenticated request succeeds
- **WHEN** a request with a valid `Authorization: Token <key>` header hits any `/apis/artworks/` endpoint
- **THEN** the response SHALL be `200 OK` with the requested resource.

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

### Requirement: API routing under /apis/artworks/
The system SHALL use a DRF `DefaultRouter` registered in `artworks/urls.py` and mounted at `apis/artworks/` from `project/urls.py`. The router root SHALL return the list of registered endpoint names and URLs.

#### Scenario: Router root lists all endpoints
- **WHEN** `GET /apis/artworks/` is requested with authentication
- **THEN** the response SHALL list all 10 registered viewset names and their URLs.

#### Scenario: URL prefix matches specification
- **WHEN** any endpoint is requested
- **THEN** the URL SHALL begin with `/apis/artworks/` (plural on both parts).

### Requirement: All list responses use project pagination
Every list endpoint SHALL use the project's `CustomPageNumberPagination` with `page_size=12`, `page_size_query_param="page_size"`, and `max_page_size=100`. The pagination envelope SHALL contain `count`, `next`, `previous`, `page`, `page_size`, `total_pages`, and `results`.

#### Scenario: Default page size
- **WHEN** a list endpoint is requested without `page_size` parameter
- **THEN** the response SHALL contain 12 items per page (or fewer on the last page).

#### Scenario: Custom page size respected
- **WHEN** `GET /apis/artworks/artworks/?page_size=50` is requested
- **THEN** the response SHALL contain up to 50 items per page.

### Requirement: Error responses use project format
All error responses SHALL use the project's `custom_exception_handler` envelope: `{status: "error", message: "<description>", data: {...}}`.

#### Scenario: 404 detail returns error envelope
- **WHEN** `GET /apis/artworks/artworks/9999/` is requested and the artwork does not exist
- **THEN** the response SHALL be `404` with the `{status, message, data}` envelope.

### Requirement: All querysets filter active rows
Every viewset queryset SHALL include `.filter(is_active=True)`. Inactive rows SHALL never appear in any API response — including nested related objects. The Artwork queryset SHALL additionally filter `artist__is_active=True`. Nested collections SHALL be filtered to active rows (both through/link rows and targets, where the row carries an `is_active` field), and single-FK refs (`Artist.location`, `Gallery.curator`) SHALL resolve to `null` when the referenced row is inactive.

#### Scenario: Inactive taxonomy term excluded
- **WHEN** a Discipline has `is_active=False`
- **THEN** that discipline SHALL NOT appear in the disciplines list endpoint.

#### Scenario: Inactive nested rows excluded
- **WHEN** an active row references inactive related objects (gallery links, artwork links, images, social links, or taxonomy terms)
- **THEN** those inactive objects SHALL NOT appear in the API response.

#### Scenario: Inactive single-FK refs resolve to null
- **WHEN** an active Artist references an inactive Location or an active Gallery references an inactive ArtCurator
- **THEN** the corresponding ref field SHALL be `null`.

#### Scenario: Artwork of inactive artist excluded
- **WHEN** an active artwork references an Artist with `is_active=False`
- **THEN** the artwork SHALL NOT appear in the artworks list endpoint.

### Requirement: Image URLs use get_media_url
All image fields (`Artist.photo`, `ArtCurator.photo`, `Gallery.logo`, `ArtworkImage.image`) SHALL be serialized as absolute URLs using `get_media_url()` from `utils/media.py`. The project SHALL define `HOST` in `project/settings.py` (from the `HOST` environment variable) so the local-prefix branch of `get_media_url()` works. The env-specific dotenv file (`.env.{ENV}`) SHALL be loaded with `override=True` so project-defined values take precedence over shell-injected vars.

#### Scenario: HOST setting defined
- **WHEN** `project/settings.py` is loaded
- **THEN** it SHALL expose a `HOST` attribute read from the `HOST` environment variable.

#### Scenario: Env-specific dotenv overrides shell vars
- **WHEN** a shell-injected env var (e.g., from `portless`) conflicts with `.env.{ENV}`
- **THEN** the value from `.env.{ENV}` SHALL take precedence.

#### Scenario: Local media prefixed with HOST
- **WHEN** an artwork image is stored locally (not S3/DigitalOcean)
- **THEN** the image URL SHALL be prefixed with `settings.HOST`.

#### Scenario: S3 URLs passed through unchanged
- **WHEN** an image is stored on S3 or DigitalOcean Spaces
- **THEN** the image URL SHALL be returned as-is (the full object URL).

#### Scenario: Missing HOST falls back to relative URL
- **WHEN** `settings.HOST` is `None` or empty
- **THEN** `get_media_url` SHALL return the relative URL (e.g., `/media/artworks/obra-1.jpg`) without crashing.

### Requirement: Translation fields exclude blank values
Each translation entry in the `{language: {field: value}}` dict SHALL only include fields with truthy values. Empty strings and `None` SHALL be omitted from the inner dict.

#### Scenario: Empty bio omitted from translations
- **WHEN** an ArtistTranslation has `bio=""` (empty string)
- **THEN** the translation entry for that language SHALL NOT include a `bio` key.

#### Scenario: Partial translation has only non-empty fields
- **WHEN** a GalleryTranslation has `name="Galería X"` and `description=""`
- **THEN** the translation entry SHALL contain only `{name: "Galería X"}`.
