# Public Catalog API Specification (Delta)

## Purpose

This delta spec captures the removal of the monolithic `GET /api/catalog/` endpoint, replaced by the 10 per-model endpoints defined in `artworks-rest-api`.

## REMOVED Requirements

### Requirement: Authenticated catalog endpoint
**Reason**: Replaced by individual model endpoints under `/apis/artworks/` (see `artworks-rest-api` spec). The monolithic endpoint combined all data into a single response, preventing selective fetching and RESTful access patterns.

**Migration**: Consumers of `GET /api/catalog/` MUST migrate to the 10 per-model endpoints. The catalog payload's top-level keys map to individual endpoints:
- `catalog.artists` → `GET /apis/artworks/artists/`
- `catalog.taxonomies.disciplines` → `GET /apis/artworks/disciplines/`
- `catalog.taxonomies.techniques` → `GET /apis/artworks/techniques/`
- `catalog.taxonomies.themes` → `GET /apis/artworks/themes/`
- `catalog.taxonomies.formats` → `GET /apis/artworks/formats/`
- `catalog.taxonomies.scales` → `GET /apis/artworks/scales/`
- `catalog.locations` → `GET /apis/artworks/locations/`
- `catalog.artworks` → `GET /apis/artworks/artworks/`

Each new endpoint is paginated. Consumers must paginate through results or use `?page_size=100` (the maximum). Response shapes differ structurally (nested translations replace flat `name_es`/`name_en` fields; taxonomy references use `{id, slug}` objects instead of ID arrays).

### Requirement: Catalog only includes buyable artworks
**Reason**: Superseded. The new Artwork endpoint filters `is_active=True` but does not filter by `status`. Buyable filtering (`status="available"`) is the consumer's responsibility. This allows the same API to serve admin/dashboard use cases beyond just the public catalog.

**Migration**: Filter artwork results client-side: `artworks.filter(a => a.status === "available")`.

### Requirement: Catalog response structure
**Reason**: The monolithic top-level response (`generated_at`, `artists`, `taxonomies`, `locations`, `artworks`) is replaced by individual paginated endpoints, each with its own response shape.

**Migration**: Compose the catalog structure from individual endpoint responses. The `generated_at` timestamp is no longer provided; consumers can use response headers or generate their own.

### Requirement: Category reference entries carry both languages
**Reason**: The flat `name_es`/`name_en` pattern is replaced by nested `translations: {es: {name}, en: {name}}` dicts on each resource.

**Migration**: Access names via `resource.translations.es.name` and `resource.translations.en.name` instead of `resource.name_es` and `resource.name_en`.

### Requirement: Artwork entries are denormalized for faceting
**Reason**: Artwork entries now use `{id, slug}` nested objects for taxonomy references instead of ID arrays, and nested translations instead of flat bilingual fields.

**Migration**: Access taxonomy references as `artwork.disciplines.map(d => d.id)` instead of `artwork.disciplines`. Access titles as `artwork.translations.es.title` instead of `artwork.title_es`.

### Requirement: Catalog is stable for the frontend contract
**Reason**: The catalog endpoint no longer exists. Contract stability is now per-endpoint, each following REST conventions with the standard pagination envelope.

**Migration**: Update SSG build code to fetch from individual endpoints and compose the catalog structure client-side.
