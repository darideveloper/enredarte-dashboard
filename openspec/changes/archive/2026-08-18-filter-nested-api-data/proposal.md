## Why

Every `/apis/artworks/` endpoint filters its own queryset to `is_active=True`, but the nested
related objects it serializes are not filtered: an active Gallery can expose links to inactive
artworks, an active Artwork can expose links to inactive galleries, and single-FK refs
(curator, location, artist) plus collections (`social_links`, `images`, taxonomy M2Ms) leak
inactive rows. Because nested refs are `{id, slug}` only, consumers cannot even see the
`is_active` flag to filter client-side. The promise "Inactive rows SHALL never appear in any
API response" currently only holds at the top level.

## What Changes

- **Filter all nested collections to active rows** across the Artist, Gallery, and Artwork
  endpoints: `social_links`, `images`, taxonomy M2Ms (`disciplines`, `techniques`, `themes`,
  `formats`, `scales`), and the through-model link sets (`gallery_links`, `artwork_links`)
  — including the link rows themselves, which are `BaseModel`s.
- **Null out inactive single-FK refs**: `Artist.location` and `Gallery.curator` return
  `null` when the referenced row is inactive (they already allow `null`).
- **Hide artworks whose artist is inactive**: the Artwork queryset additionally filters
  `artist__is_active=True`, so a deactivated artist's works leave the API instead of
  appearing with a broken/`null` artist ref.
- **No change** to the deliberate non-filter on `Artwork.status` (buyable filtering stays a
  consumer responsibility) or to endpoints with no nested objects (ArtCurator, Location,
  taxonomies, translations).

## Capabilities

### New Capabilities

- `nested-active-filtering`: nested/related objects serialized by the artworks REST API are
  filtered to active rows, recursively matching the top-level `is_active=True` contract.

### Modified Capabilities

- `artworks-rest-api`: the "All querysets filter active rows" requirement is extended from
  top-level querysets to all nested related objects (collections, through-model links, and
  single-FK refs).

## Impact

- `artworks/views.py`: Artist, Gallery, and Artwork viewsets switch to `get_queryset()` with
  filtered `Prefetch` objects (`select_related` for single FKs to avoid N+1).
- `artworks/serializers.py`: new reusable `ActiveRefField` for `location`/`curator` refs.
- `artworks/tests.py`: `ArtworksAPITestCase` gains nested-filtering coverage.
- API response shape: nested collections may shrink; `location`/`curator` may become `null`;
  artworks referencing inactive artists disappear. No breaking field removals.