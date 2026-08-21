## Context

The `blog` application contains `Post` and `PostTranslation` models with bilingual titles, descriptions, keywords, and Markdown content. To enable the frontend / static site generators to display both a blog index (card grid / previews) and full article reader pages, we need dedicated read-only endpoints in Django Rest Framework.

## Goals / Non-Goals

**Goals:**
- Implement `PostSummarySerializer` providing flattened bilingual fields (`title_es`, `title_en`, `description_es`, `description_en`, `keywords_es`, `keywords_en`), author, banner image URL, and publication timestamp without heavy markdown bodies.
- Implement `PostDetailSerializer` inheriting from `PostSummarySerializer` and appending bilingual markdown content (`content_es`, `content_en`).
- Implement `PostViewSet` (`ReadOnlyModelViewSet`) with `lookup_field = "slug"`, public read access (`AllowAny`), active-only filtering (`is_active=True`), chronological ordering (`-published_at, sort_order, -id`), and query prefetching (`.prefetch_related("translations")`).
- Use DRF's global `CustomPageNumberPagination` for the list endpoint (`/api/blog/posts/`) with configurable `?page=` and `?page_size=`.
- Expose endpoints via `blog/urls.py` mounted at `/api/blog/` in `project/urls.py`.

**Non-Goals:**
- Write/update/delete operations via API (all content management is performed via Unfold Admin).
- Language query filtering (both Spanish and English data are returned together for maximum client-side flexibility).
- Standalone seed fixtures (handled in next proposal `blog-fixtures-tests`).

## Decisions

### 1. ViewSet with Dynamic Action-Based Serializer Selection
- **Decision**: Use `ReadOnlyModelViewSet` with `lookup_field = "slug"` and override `get_serializer_class()`:
  ```python
  def get_serializer_class(self):
      if self.action == "retrieve":
          return PostDetailSerializer
      return PostSummarySerializer
  ```
- **Rationale**: Clean, idiomatic REST structure that leverages DRF's built-in routers, automatic schema generation, and automatic pagination on `list` while delivering light payloads on grids and full payloads on single articles.

### 2. Flattened Bilingual Naming Convention
- **Decision**: Use `_translation_value(obj, language, attr)` helper to extract `*_es` and `*_en` fields directly on the root post JSON object.
- **Rationale**: Matches `artworks/serializers.py` (`ArtworkSerializer`), making integration straightforward for frontends without nested translation drilling.

### 3. Automatic Global Pagination
- **Decision**: Rely on DRF default pagination (`project.pagination.CustomPageNumberPagination`).
- **Rationale**: Returns standardized pagination envelope (`count`, `next`, `previous`, `page`, `page_size`, `total_pages`, `results`) to ensure fast page loads as the post library grows.

## Risks / Trade-offs

- **[Risk] N+1 Query in List and Detail Responses**: Accessing `translations` on each post could produce separate SQL queries.
  - **Mitigation**: Add `.prefetch_related("translations")` to `get_queryset()`.
- **[Risk] Draft/Inactive Posts Leak**: Unpublished or inactive posts could be publicly visible.
  - **Mitigation**: Restrict `get_queryset()` strictly to `Post.objects.filter(is_active=True)`.
