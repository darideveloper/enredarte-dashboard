## Context

The project has 10 domain models in `artworks/models.py` with a translation-row i18n pattern (Spanish/English). Currently a single `CatalogAPIView` at `GET /api/catalog/` returns everything denormalized and unpaginated using hand-rolled `Serializer` classes. DRF is configured with `TokenAuthentication`, `PageNumberPagination`, and a custom error handler, but the `DefaultRouter` in `project/urls.py` has zero registered viewsets.

The goal is to expose each model as a separate read-only paginated endpoint under `/apis/artworks/`, with translations nested in the response, sub-objects inlined, and cross-model FK/M2M references serialized as lightweight `{id, slug}` objects.

## Goals / Non-Goals

**Goals:**
- 10 per-model read-only endpoints, each serving list + detail (paginated lists, full-resource detail)
- Nested translations as `{language: {field: value}}` dicts for every model with translations
- Inlined sub-objects: `Artist.social_links`, `Artwork.images`, `Artwork.gallery_links`, `Gallery.artwork_links`
- Cross-model FK/M2M references as `{id, slug}` objects (not nested full resources)
- All querysets filtered `is_active=True` by default
- Absolute image URLs via `get_media_url()` from `utils/media.py`
- Bruno API collection updated with 20 request files (10 folders × list + detail)
- Token authentication on all endpoints (same existing `IsAuthenticated` default)

**Non-Goals:**
- CRUD/write support — read-only only
- Filtering/sorting query params
- Search
- Auth endpoint or token management
- Model or database changes
- Admin changes
- Migration changes

## Decisions

### 1. ReadOnlyModelViewSet + ModelSerializer over APIView

DRF's `ReadOnlyModelViewSet` provides `list()` and `retrieve()` out of the box with built-in pagination, prefetch-compatible querysets, and automatic router registration. Writing 10 separate `APIView` subclasses would duplicate boilerplate (pagination wiring, queryset prefetch, serializer instantiation with context).

A shared `BaseReadOnlyViewSet(ReadOnlyModelViewSet)` base class isn't needed here — each viewset just needs a `queryset` and `serializer_class`, with `get_queryset()` overridden only for models needing custom prefetch (Artwork, Artist, Gallery). The five identical taxonomy viewsets (Discipline, Technique, Theme, Format, Scale) reuse a small `_TaxonomyViewSet` base that serves the same `is_active=True` + `translations` prefetch queryset via a `model` attribute; the router registers them with explicit `basename`s since they expose no `queryset` class attribute. The default `ReadOnlyModelViewSet` handles the rest.

`ModelSerializer` generates field declarations from the model's field types — no need to manually declare `id = serializers.IntegerField()` for 50+ fields across 10 serializers. Only special handling (translation nesting, FK refs, image URLs) requires explicit field declarations.

### 2. Translation nesting: SerializerMethodField

Each parent model has a `translations` related manager (e.g., `artist.translations.all()`). A `SerializerMethodField` on each serializer calls a shared helper that converts the queryset to `{language: {field: value}}`:

```python
def _build_translation_dict(translations, fields):
    return {
        t.language: {f: getattr(t, f) for f in fields if getattr(t, f, None)}
        for t in translations
    }
```

Four translation field-sets exist across the 10 models:
- `{es: {name}, en: {name}}` — Location, Discipline, Technique, Theme, Format, Scale
- `{es: {name, description}, en: {name, description}}` — Gallery
- `{es: {bio}, en: {bio}}` — Artist, ArtCurator
- `{es: {title, description}, en: {title, description}}` — Artwork

Blank fields (empty strings) are excluded via `if getattr(t, f, None)` to keep responses clean.

### 3. Cross-model references: single RefSerializer

Every main model extends `BaseModel`, which has `id` and `slug`. A single generic serializer handles all FK and M2M references:

```python
class RefSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    slug = serializers.CharField()
```

Used for:
- `Artist.location`, `Gallery.curator`, `Artwork.artist` (FK → RefSerializer)
- `Artwork.disciplines`, `.techniques`, `.themes`, `.formats`, `.scales` (M2M → RefSerializer(many=True))
- `ArtworkGallery.artwork`, `.gallery` (FK → RefSerializer, used inside inlined sub-objects)

This is a plain `Serializer`, not a `ModelSerializer`, because it serializes any model instance (polymorphic by duck typing — any object with `id` and `slug` attributes works).

### 4. Image URLs: get_media_url() wrapper

`utils/media.py` exports `get_media_url(obj)` that returns an absolute URL, prefixing with `settings.HOST` for local files and passing through S3/DigitalOcean URLs unchanged.

ModelSerializer's default `ImageField` serialization returns a relative path. Instead, each image field is declared as:

```python
photo = serializers.SerializerMethodField()

def get_photo(self, obj):
    return get_media_url(obj.photo) if obj.photo else None
```

This affects: `Artist.photo`, `ArtCurator.photo`, `Gallery.logo`, `ArtworkImage.image`.

Note: `settings.HOST` is currently **not defined** in `project/settings.py` (only declared in env files), so `get_media_url()` raises `AttributeError` for local files. This change adds `HOST = os.getenv("HOST")` to `project/settings.py` (one line) so the local-prefix branch works; S3 passthrough is unaffected.

### 5. Numeric prices

`ModelSerializer` maps `DecimalField` to a string by default (`coerce_to_string=True`). To match the catalog contract (`price_mxn`/`price_usd` as JSON numbers), `ArtworkSerializer` declares them explicitly:

```python
price_mxn = serializers.DecimalField(max_digits=10, decimal_places=2, coerce_to_string=False)
price_usd = serializers.DecimalField(max_digits=10, decimal_places=2, coerce_to_string=False)
```

### 6. Prefetch strategy

Each ViewSet's `get_queryset()` is responsible for minimizing N+1 queries:

| ViewSet | Prefetch |
|---------|----------|
| Artist | `location`, `translations`, `social_links` |
| ArtCurator | `translations` |
| Location | `translations` |
| Gallery | `curator`, `translations`, `artwork_links__artwork` |
| Discipline, Technique, Theme, Format, Scale | `translations` |
| Artwork | `artist`, `disciplines`, `techniques`, `themes`, `formats`, `scales`, `translations`, `images`, `gallery_links__gallery` |

Taxonomy models (Discipline/Technique/Theme/Format/Scale) have no FK or sub-object refs — they only need `translations` prefetched. Location is identical.

### 7. is_active filtering

All querysets filter `is_active=True` by default, matching the existing catalog behavior. The base viewset queryset attribute includes the filter:

```python
class ArtistViewSet(ReadOnlyModelViewSet):
    queryset = Artist.objects.filter(is_active=True).prefetch_related(...)
```

Inactive rows are never served by the API. The `is_active` field itself is still included in the response so consumers can see the flag value (always `True`).

### 8. File organization

The project is dashboard + APIs only, so the API layer lives directly in the `artworks` app (no `apis/` subpackage):

```
artworks/
├── serializers.py    # RefSerializer, translation helper, 10 ModelSerializers
├── views.py          # 10 ReadOnlyModelViewSets, each with prefetch get_queryset
└── urls.py           # DefaultRouter with 10 registrations

project/urls.py       # path("apis/artworks/", include("artworks.urls"))
```

`views.py` imports serializers from `serializers.py`. `urls.py` imports views from `views.py`. No circular dependency — standard DRF pattern.

## Risks / Trade-offs

- **Breaking change for SSG build**: The old `GET /api/catalog/` returned all data unpaginated for static site generation. The new approach requires the SSG build to paginate through 10 endpoints. Mitigation: the existing `max_page_size=100` can be used to reduce requests (e.g., `?page_size=100`), but the build will need code changes regardless.

- **No filtering means client-side discovery**: Without `?artist_id=` filters on artworks, a frontend that needs "all artworks by artist X" must paginate through the entire artworks list and filter client-side. Mitigation: artworks are paginated in`sort_order` order, so nearby artworks often share taxonomy context. If this becomes painful, filtering can be added later (out of scope for this change).

- **ArtworkGallery appears in both Artwork and Gallery**: The same M2M-through row is inlined in both parent endpoints. This is denormalized but mirrors the data model accurately. No risk of inconsistency since it's read-only.

- **Translation data always prefetched**: Every request prefetches translations even if the consumer doesn't need them in that language. The overhead is negligible (2 rows × 10-12 items per page) and simplifies the serializer by avoiding conditional translation inclusion.
