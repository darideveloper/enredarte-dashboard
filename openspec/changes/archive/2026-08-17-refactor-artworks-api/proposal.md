## Why

The current API exposes a single monolithic `GET /api/catalog/` endpoint that returns all buyable artworks, artists, taxonomy terms, and locations denormalized in one unpaginated response. This serves the SSG build but prevents selective data fetching, complicates caching, and offers no RESTful per-model access. A frontend that only needs locations must download the entire catalog. Separating each model into its own read-only, paginated endpoint under `/apis/artworks/` enables granular consumption, follows REST conventions, and reuses the existing token authentication.

## What Changes

- **Remove** `CatalogAPIView` (`artworks/views.py`) and its route (`/api/catalog/`). **BREAKING**: any consumer of the monolithic catalog endpoint must migrate to individual model endpoints.
- **Remove** the old `artworks/serializers.py` (3 hand-rolled `Serializer` classes) — replaced by `ModelSerializer`-based serializers in the same `artworks/serializers.py`.
- **Remove** the obsolete `PublicCatalogAPITestCase` from `artworks/tests.py` (3 tests hitting the deleted `/api/catalog/`).
- **Remove** the empty DRF router registration in `project/urls.py` — replaced by a dedicated `artworks/urls.py` router.
- **Remove** all existing Bruno request files (`Auth/GET api root.bru`, `Authenticated Catalog/GET catalog.bru`).
- **Create** `artworks/serializers.py`, `artworks/views.py`, and `artworks/urls.py` (API files living directly in the `artworks` app — the project is dashboard + APIs only) implementing 10 `ReadOnlyModelViewSet` endpoints, each with `ModelSerializer`, nested translations via `{language: {field: value}}` dicts, `{id, slug}` refs for cross-model FKs, and inlined sub-objects (`ArtistSocialLink`, `ArtworkImage`, `ArtworkGallery`).
- **Create** 20 Bruno request files (10 model folders × 2 files: list + detail) under `bruno/collections/enredarte-dashboard-api/`, all using `{{base_url}}/apis/artworks/<resource>/` and token auth.
- **Filter** all querysets by `is_active=True` by default.
- **Paginate** all list responses via the existing `CustomPageNumberPagination`.
- **Generate** absolute image URLs via `get_media_url()` from `utils/media.py`.

## Capabilities

### New Capabilities
- `artworks-rest-api`: 10 per-model read-only paginated endpoints under `/apis/artworks/` (Artist, ArtCurator, Location, Gallery, Discipline, Technique, Theme, Format, Scale, Artwork), each with nested translations, inlined sub-objects, `{id, slug}` FK refs, and `is_active=True` querysets. Includes shared serialization utilities for DRY translation handling and image URL generation.
- `artworks-api-bruno`: Bruno collection with 20 request files (10 folders × 2: list + detail), replacing the old catalog and api-root requests. Uses `{{base_url}}/apis/artworks/` paths and token auth.

### Modified Capabilities
- `public-catalog-api`: **REMOVED**. Replaced by `artworks-rest-api`. The monolithic `GET /api/catalog/` endpoint, `CatalogAPIView`, and `artworks/serializers.py` are deleted. Consumers must now compose data from individual model endpoints.
- `bruno-api-collection`: **REWRITTEN**. All existing request files are deleted and replaced by per-model list/detail requests in `artworks-api-bruno`. The workspace structure (`bruno.json`, `workspace.yml`, `dev.bru` environment) is preserved.

## Impact

- **`artworks/views.py`**: rewritten — `CatalogAPIView` removed, replaced by the 10 `ReadOnlyModelViewSet`s (was 65 lines, now ~94).
- **`artworks/serializers.py`**: rewritten — 3 hand-rolled `Serializer` classes removed, replaced by `ModelSerializer`-based serializers (was 118 lines, now ~205).
- **`artworks/urls.py`**: new — DRF `DefaultRouter` with 10 registrations (~28 lines).
- **`project/urls.py`**: simplified — old catalog route and empty router removed, replaced by `path("apis/artworks/", include("artworks.urls"))`.
- **`project/settings.py`**: adds `HOST = os.getenv("HOST")` (one line), required by `get_media_url()` to build absolute local image URLs.
- **`artworks/tests.py`**: `PublicCatalogAPITestCase` removed (obsolete catalog tests).
- **`bruno/`**: 2 old request files removed, 20 new files created, `dev.bru` environment preserved, `README.md` updated.
- **`docs/django-drf.md` and `docs/django-bruno.md`**: updated — catalog references replaced with the new per-model endpoints and `/apis/artworks/` prefix.
- **Zero database changes**, zero model changes, zero migration changes.
