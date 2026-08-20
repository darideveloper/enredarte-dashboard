## Why

Now that blog models and admin interfaces are established, the platform needs public REST API endpoints to serve blog content to client applications, static site generators, and frontend interfaces. The API must provide two primary data views: a paginated summary list for blog card grids/previews and a detailed view for full article pages with bilingual markdown content, without requiring language query filtering.

## What Changes

- Implement DRY DRF serializers in `blog/serializers.py`:
  - `PostSummarySerializer`: Serializes post metadata (`id`, `slug`, `author`, `banner_image`, `published_at`, `sort_order`) and flattened bilingual fields (`title_es`, `title_en`, `description_es`, `description_en`, `keywords_es`, `keywords_en`).
  - `PostDetailSerializer`: Inherits from `PostSummarySerializer` and adds full bilingual markdown content (`content_es`, `content_en`).
- Implement `PostViewSet` (`ReadOnlyModelViewSet`) in `blog/views.py`:
  - Public read-only access (`permission_classes = [AllowAny]`).
  - Query filtering for active posts (`is_active=True`) ordered by `-published_at, sort_order, -id`.
  - Slug-based lookup (`lookup_field = "slug"`) for retrieving single articles.
  - Action-based serializer switching (`PostSummarySerializer` for list, `PostDetailSerializer` for retrieve).
  - Query optimization via `.prefetch_related("translations")`.
- Register blog routes in `blog/urls.py` and mount under `/api/blog/` in `project/urls.py`.

## Capabilities

### New Capabilities
- `blog-apis`: Public REST API endpoints for blog post listing (summary/pagination) and detail retrieval (full markdown content by slug).

### Modified Capabilities
<!-- None -->

## Impact

- `blog/serializers.py`: New serializers module for blog post payloads.
- `blog/views.py`: New viewset module for blog post endpoints.
- `blog/urls.py`: New routing configuration for the `blog` app.
- `project/urls.py`: Mounts `blog/urls.py` under `api/blog/`.
- Frontend consumers and SSG builders will consume `GET /api/blog/posts/` and `GET /api/blog/posts/{slug}/`.
