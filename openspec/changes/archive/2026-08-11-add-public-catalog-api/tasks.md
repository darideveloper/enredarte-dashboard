## 1. Serializers

- [x] 1.1 Create `artworks/serializers.py` with a taxonomy/location ref serializer producing `id`, `slug`, `name_es`, `name_en` (es-first fallback, then slug), using queried translations; plus an artist ref serializer producing `id`, `slug`, `name_es`, `name_en` (both resolved from `Person.name` — artists have no name translation) and `location_id`.
- [x] 1.2 Add an artwork serializer producing the denormalized entry: `id`, `slug`, `title_es`, `title_en`, `image`, `image_alt_es`, `image_alt_en`, `artist_id`, `year`, `dimensions`, `price_mxn`, `price_usd`, and the five taxonomy id arrays.
- [x] 1.3 Implement the primary-image resolution helper (primary flag first, else first by `sort_order`; `null` when none) and the bilingual alt-text resolution (`alt_es`/`alt_en`, falling back to the translated title) in the serializer.

## 2. View

- [x] 2.1 Add `CatalogAPIView(APIView)` in `artworks/views.py` with `permission_classes = [AllowAny]` and `pagination_class = None`.
- [x] 2.2 Build the queryset filtered to `is_active=True` and `status=ArtworkStatus.AVAILABLE`, with `prefetch_related` for the five M2Ms, `translations`, and `images`, plus `select_related("artist", "artist__location")`.
- [x] 2.3 Compose the response object: `generated_at`, `artists`, `taxonomies` (all five groups, ordered by `sort_order`), `locations`, `artworks`.

## 3. Routing

- [x] 3.1 Register `GET /api/catalog/` in `project/urls.py` pointing to `CatalogAPIView`.

## 4. Tests

- [x] 4.1 Add DRF `APITestCase` verifying the endpoint returns `200` with no auth, and that the response is not paginated.
- [x] 4.2 Add tests asserting sold/reserved/on-loan/inactive artworks are excluded and available artworks are included.
- [x] 4.3 Add tests asserting presence of all top-level keys (including `locations`) and all five taxonomy groups (including empty groups).
- [x] 4.4 Add tests asserting bilingual names/fallbacks, `location_id` + top-level `locations` list, `sort_order` ordering, primary-image selection and fallback, bilingual `image_alt_es`/`image_alt_en`, and the five taxonomy id arrays.

## 5. Verification

- [x] 5.1 Run the full backend test suite (`python manage.py test`) and ensure all tests pass.
- [x] 5.2 Run a local curl against `/api/catalog/` and confirm the payload matches the spec contract, then summarize the change for the frontend repo.