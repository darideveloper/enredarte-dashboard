## 1. Serializers & Views Implementation

- [x] 1.1 Implement `PostSummarySerializer` and `PostDetailSerializer` with bilingual helper in `blog/serializers.py`
- [x] 1.2 Implement `PostViewSet` (`ReadOnlyModelViewSet`) with slug lookup, active filtering, ordering, and translation prefetching in `blog/views.py`
- [x] 1.3 Register `PostViewSet` in `blog/urls.py` and include under `/api/blog/` in `project/urls.py`

## 2. Automated & External Verification

- [x] 2.1 Write comprehensive DRF unit tests in `blog/tests.py` covering list pagination, detail by slug, active filtering, and 0 N+1 queries
- [x] 2.2 Verify live HTTP endpoints externally using `curl` against both summary list and detail endpoints
