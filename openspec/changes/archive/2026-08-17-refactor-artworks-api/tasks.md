## 1. Cleanup — Remove old API code

- [x] 1.1 Remove `CatalogAPIView` from `artworks/views.py` (rewritten for the new API viewsets, was 65 lines)
- [x] 1.2 Remove the 3 hand-rolled `Serializer` classes from `artworks/serializers.py` (rewritten with `ModelSerializer`s, was 118 lines)
- [x] 1.3 Delete `bruno/collections/enredarte-dashboard-api/Auth/GET api root.bru`
- [x] 1.4 Delete `bruno/collections/enredarte-dashboard-api/Authenticated Catalog/GET catalog.bru`
- [x] 1.5 Update `project/urls.py`: remove `from artworks.views import CatalogAPIView` import, the `api/catalog/` route, and the empty `router` registration
- [x] 1.6 Remove `PublicCatalogAPITestCase` from `artworks/tests.py` (obsolete tests hitting `/api/catalog/`)

## 2. Prepare API files

- [x] 2.1 Confirm the API layer lives directly in the `artworks` app (no `apis/` subpackage): `artworks/serializers.py`, `artworks/views.py`, `artworks/urls.py`
- [x] 2.2 Add `HOST = os.getenv("HOST")` to `project/settings.py` (required by `get_media_url()` for absolute local image URLs)

## 3. API Serializers

- [x] 3.1 Create `artworks/serializers.py` with shared utilities:
  - `_build_translation_dict(translations, fields)` helper
  - `RefSerializer` (generic `{id, slug}` for FK/M2M refs)
- [x] 3.2 Add `ArtistSerializer` (ModelSerializer: all Person fields + photo via `get_media_url`, location as RefSerializer, translations as `{es/en: {bio}}`, social_links inline)
- [x] 3.3 Add `ArtCuratorSerializer` (ModelSerializer: all Person fields + photo via `get_media_url`, translations as `{es/en: {bio}}`)
- [x] 3.4 Add `LocationSerializer` (ModelSerializer: BaseModel fields, translations as `{es/en: {name}}`)
- [x] 3.5 Add `GallerySerializer` (ModelSerializer: BaseModel fields + logo via `get_media_url`, curator as RefSerializer, translations as `{es/en: {name, description}}`, artwork_links inline)
- [x] 3.6 Add taxonomy serializers — `DisciplineSerializer`, `TechniqueSerializer`, `ThemeSerializer`, `FormatSerializer`, `ScaleSerializer` (all identical: BaseModel fields + translations as `{es/en: {name}}`)
- [x] 3.7 Add `ArtworkSerializer` (ModelSerializer: all fields, artist as RefSerializer, M2M taxonomy fields as RefSerializer(many=True), translations as `{es/en: {title, description}}`, images inline with `get_media_url`, gallery_links inline, and `price_mxn`/`price_usd` as `DecimalField(max_digits=10, decimal_places=2, coerce_to_string=False)` for numeric JSON output)
- [x] 3.8 Add `ArtworkImageSerializer` (for inlining: id, image via `get_media_url`, alt_es, alt_en, is_primary, sort_order)
- [x] 3.9 Add `ArtistSocialLinkSerializer` (for inlining: id, platform, url)
- [x] 3.10 Add `ArtworkGalleryLinkSerializer` (for inlining: id, gallery as RefSerializer, sort_order)
- [x] 3.11 Add `GalleryArtworkLinkSerializer` (for inlining: id, artwork as RefSerializer, sort_order)

## 4. API Views

- [x] 4.1 Create `artworks/views.py` with 10 `ReadOnlyModelViewSet` subclasses, each setting `queryset` (with `is_active=True` filter + required prefetch + `.order_by("sort_order")`) and `serializer_class`
- [x] 4.2 Artist viewset: `.filter(is_active=True).prefetch_related("location", "translations", "social_links").order_by("sort_order")`
- [x] 4.3 ArtCurator viewset: `.filter(is_active=True).prefetch_related("translations").order_by("sort_order")`
- [x] 4.4 Location viewset: `.filter(is_active=True).prefetch_related("translations").order_by("sort_order")`
- [x] 4.5 Gallery viewset: `.filter(is_active=True).prefetch_related("curator", "translations", "artwork_links__artwork").order_by("sort_order")`
- [x] 4.6 Discipline, Technique, Theme, Format, Scale viewsets: `.filter(is_active=True).prefetch_related("translations").order_by("sort_order")`
- [x] 4.7 Artwork viewset: `.filter(is_active=True).prefetch_related("artist", "disciplines", "techniques", "themes", "formats", "scales", "translations", "images", "gallery_links__gallery").order_by("sort_order")`

## 5. URL Routing

- [x] 5.1 Create `artworks/urls.py` with `DefaultRouter`, register all 10 viewsets with prefixes `artists`, `art-curators`, `locations`, `galleries`, `disciplines`, `techniques`, `themes`, `formats`, `scales`, `artworks`, export `urlpatterns = router.urls`
- [x] 5.2 Update `project/urls.py`: add `path("apis/artworks/", include("artworks.urls"))` route (cleanup already done in 1.5)

## 6. Bruno API Collection

- [x] 6.1 Create `bruno/collections/enredarte-dashboard-api/Artists/GET list.bru` (URL: `{{base_url}}/apis/artworks/artists/`)
- [x] 6.2 Create `bruno/collections/enredarte-dashboard-api/Artists/GET detail.bru` (URL: `{{base_url}}/apis/artworks/artists/1/`)
- [x] 6.3 Create `bruno/collections/enredarte-dashboard-api/ArtCurators/GET list.bru` and `GET detail.bru`
- [x] 6.4 Create `bruno/collections/enredarte-dashboard-api/Locations/GET list.bru` and `GET detail.bru`
- [x] 6.5 Create `bruno/collections/enredarte-dashboard-api/Galleries/GET list.bru` and `GET detail.bru`
- [x] 6.6 Create `bruno/collections/enredarte-dashboard-api/Disciplines/GET list.bru` and `GET detail.bru`
- [x] 6.7 Create `bruno/collections/enredarte-dashboard-api/Techniques/GET list.bru` and `GET detail.bru`
- [x] 6.8 Create `bruno/collections/enredarte-dashboard-api/Themes/GET list.bru` and `GET detail.bru`
- [x] 6.9 Create `bruno/collections/enredarte-dashboard-api/Formats/GET list.bru` and `GET detail.bru`
- [x] 6.10 Create `bruno/collections/enredarte-dashboard-api/Scales/GET list.bru` and `GET detail.bru`
- [x] 6.11 Create `bruno/collections/enredarte-dashboard-api/Artworks/GET list.bru` and `GET detail.bru`
- [x] 6.12 Update `bruno/README.md` to document the new endpoint structure

## 7. Documentation

- [x] 7.1 Update `docs/django-drf.md`: replace `/api/catalog/` references with the 10 per-model endpoints under `/apis/artworks/` and the updated SSG build token flow
- [x] 7.2 Update `docs/django-bruno.md`: replace the catalog request example with the per-model request files under `/apis/artworks/`

## 8. Verification

- [x] 8.1 Run `python manage.py check` to verify no import errors or misconfigurations
- [x] 8.2 Run `python manage.py test artworks` to confirm the suite passes after removing the catalog tests
- [x] 8.3 Test `GET /apis/artworks/` (router root) returns 200 with token auth
- [x] 8.4 Spot-check 3 endpoints: `GET /apis/artworks/artworks/`, `GET /apis/artworks/artists/`, `GET /apis/artworks/disciplines/`
- [x] 8.5 Verify `GET /apis/artworks/` returns 401 without token
- [x] 8.6 Verify old `/api/catalog/` returns 404 (route removed)
- [x] 8.7 Verify image URLs are absolute (check `photo`, `logo`, `image` fields in responses)
