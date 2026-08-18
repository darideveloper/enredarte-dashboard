## Context

The artworks REST API (`artworks/views.py`) exposes 10 read-only viewsets, each already
filtering its top-level queryset with `.filter(is_active=True)`. Nested data is served via
`prefetch_related(...)` plus `many=True, read_only=True` serializer fields and `{id, slug}`
`RefSerializer` refs. Nothing filters the nested side, so inactive related rows leak through:
`Gallery.artwork_links`, `Artwork.gallery_links`, `Artwork.images`, taxonomy M2Ms,
`Artist.social_links`, and the single-FK refs `Artist.location`, `Gallery.curator`,
`Artwork.artist`. `ArtworkImage`, `ArtworkGallery`, and `ArtistSocialLink` all extend
`BaseModel`, so they carry their own `is_active`.

Consumers (the SSG catalog build) compose a catalog from these endpoints; nested refs are
`{id, slug}` with no `is_active` flag, so inactive leaks are invisible to them.

## Goals / Non-Goals

**Goals:**
- Every related object serialized by the API is `is_active=True` — recursively, not just
  top level.
- Single-FK refs that point at inactive rows resolve to `null` (`location`, `curator`).
- Artworks whose artist is inactive are excluded from `/apis/artworks/`.
- No N+1 regressions; related data stays fully prefetched.
- Minimal, pattern-following diff reusing DRF `Prefetch` and the existing serializers.

**Non-Goals:**
- Filtering by `Artwork.status` (buyable filtering stays a consumer responsibility).
- Filtering `translations` (they have no `is_active`).
- Touching ArtCurator / Location / taxonomy endpoints (no nested objects beyond
  translations).
- Admin-side filtering (already correct via annotated counts).

## Decisions

### 1. Filtered `Prefetch` querysets in the three complex viewsets

`ArtistViewSet`, `GalleryViewSet`, and `ArtworkViewSet` move from a class-attr `queryset` to
`get_queryset()` that builds filtered `Prefetch` objects:

- `social_links` → `Prefetch("social_links", queryset=ArtistSocialLink.objects.filter(is_active=True))`
- `images` → `Prefetch("images", queryset=ArtworkImage.objects.filter(is_active=True).order_by("sort_order"))`
- taxonomy M2Ms → one `Prefetch` each with `Model.objects.filter(is_active=True)`
- `artwork_links` → `Prefetch("artwork_links", queryset=ArtworkGallery.objects.filter(is_active=True, artwork__is_active=True).select_related("artwork").order_by("sort_order"))`
- `gallery_links` → same pattern with `gallery__is_active=True` + `select_related("gallery")`

Filtering the link queryset (`is_active=True, artwork__is_active=True`) covers both the
through-row and the target in a single join; `select_related` keeps `RefSerializer` reads
query-free. Serializer `many=True, read_only=True` fields read `obj.<related>.all()`, which
returns the already-filtered prefetched set — no serializer changes needed for collections.

**Alternative considered:** filtering in a custom manager or overriding related managers on
the models. Rejected: touches every model for a concern that lives only in the API layer.
**Alternative considered:** a custom `get_serializer()` filtering each relation per instance.
Rejected: N+1 risk; `Prefetch` solves it in one query per relation.

### 2. `ActiveRefField` for inactive single-FK refs

Add a small field subclassing the existing `RefSerializer`:

```python
class ActiveRefField(RefSerializer):
    def to_representation(self, obj):
        if obj is None or not obj.is_active:
            return None
        return super().to_representation(obj)
```

Used for `Artist.location` and `Gallery.curator` (both already `allow_null=True`). Loading
the FK is switched from `prefetch_related("location"/"curator")` to `select_related(...)` so
the `obj.is_active` check never triggers a per-row query.

**Alternative considered:** `SerializerMethodField` per field. Rejected: duplicates logic per
serializer; the field class keeps it in one place.

### 3. Exclude artworks with an inactive artist

`ArtworkViewSet` adds `artist__is_active=True` to the queryset, so deactivated artists'
works disappear from the API entirely rather than returning a `null` artist ref (a broken
catalog entry). `Artwork.artist` is `PROTECT`, so no deleted-artist case exists.

**Alternative considered:** `ActiveRefField(allow_null=True)` on `Artwork.artist`, keeping
the artwork visible. Rejected: null-artist catalog entries are incoherent; hiding the works
is the smaller, more consistent behavior and matches "inactive rows never appear".

## Risks / Trade-offs

- [Silently smaller nested collections may surprise existing consumers] → These are catalog
  reads; shrinking to active-only is the intended contract. Nested refs keep shape; no field
  removals. Documented in specs.
- [Artworks of deactivated artists vanish] → Deliberate; the deactivation action is the
  signal. Flip to null-ref behavior in one line if a stakeholder wants works to stay visible.
- [`Prefetch` queryset must repeat ordering] → Preserved explicitly
  (`.order_by("sort_order")`) so serialized order is stable.
- [Tests currently only cover top-level exclusion] → Extended in `ArtworksAPITestCase`.

## Migration Plan

Pure behavior change in serialization and querysets — no data migration, no schema change.
Deploy as a normal code release; rollback = revert the views/serializers change.

## Open Questions

None — artist-policy decision (hide vs null) is resolved in Decision 3; the null-ref
alternative is documented there if it needs revisiting.