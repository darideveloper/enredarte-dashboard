## Context

- Backend: Django 5.2 + DRF. Global defaults are `IsAuthenticated`, custom page pagination (`page_size=12`), and a custom exception handler that wraps errors as `{status, message, data}`. The router (`project/urls.py`) registers nothing and `artworks/views.py` is empty — no public API exists today.
- Data model: `Artwork` has an `artist` FK plus five M2M taxonomies (`Discipline`, `Technique`, `Theme`, `Format`, `Scale`), `status` and `is_active`, prices in MXN/USD, and per-language text in `*Translation` rows (es/en). `ArtworkImage` carries `is_primary`, `sort_order`, and bilingual `alt_es`/`alt_en`. `Artist` is a `Person` with a plain `name` (no name translation) and a `location` FK to `Location` (a translatable name model).
- Frontend (separate Astro project, single build, per-locale routes): fetches the whole catalog once at build time, computes filter availability client-side (artists multi-select, taxonomies single-select, options disabled when they cannot produce a result), shows an empty state it already handles. Freshness relies on the existing manual/on-push rebuild.

## Goals / Non-Goals

**Goals:**
- Expose one public endpoint, `GET /api/catalog/`, that returns everything the SSG build needs in one fetch.
- Limit contents to buyable works: `is_active=True` and `status=AVAILABLE`.
- Ship names and titles in both `es` and `en` in the same payload, so the single Astro build can render both locale routes.
- Denormalized, minimal artwork items (primary image URL, bilingual alt text, artist id, taxonomy ids as arrays) so facilitacion is pure id-membership on the client.
- Route-level `AllowAny` + no pagination, overriding only this route; all other DRF behavior unchanged.
- Backend tests verifying payload shape, available-only scope, public access, and stability.

**Non-Goals:**
- Not building a general-purpose REST API for other consumers (only when a second consumer appears do we refactor into generic resources).
- Not shipping a build token / secret-based auth.
- Not implementing the frontend facet/disable logic (lives in the Astro repo).
- Not adding ISR, caching layers, or webhook-triggered rebuilds — freshness stays on the existing rebuild model.
- Not including sold/reserved pieces or artist-profile "sold" galleries; those pages get their own data later.

## Decisions

### D1 — Single composite `APIView`, not a ModelViewSet

The response is a snapshot object (artworks + artists + taxonomies + locations), not a paginated resource list. A `ModelViewSet` would fight the global paginator and cannot return the composite shape. A read-only `APIView` with `pagination_class = None` and `permission_classes = [AllowAny]` returns a plain `Response`.

- **Alternative considered:** grouped `ModelViewSet`s under the router (Approach B from exploration) — reusable but forces the frontend to assemble multiple calls and override global auth/pagination everywhere. Rejected: one consumer, one contract.

### D2 — Single route `GET /api/catalog/`

One fetch, one contract, atomic snapshot. The payload is versioned only implicitly by `generated_at`; the frontend treats it as wholesale-replaceable. If shape-breaking changes are ever needed, the endpoint moves to `/api/catalog/v2/` rather than evolving in place.

### D3 — Payload shape

```
{
  "generated_at": "2026-08-10T...Z",
  "artists":    [ { "id", "slug", "name_es", "name_en", "location_id" } ],
  "taxonomies": {
    "disciplines": [ { "id", "slug", "name_es", "name_en" } ],
    "techniques":  [ ... ], "themes": [ ... ],
    "formats":     [ ... ], "scales": [ ... ]
  },
  "locations": [ { "id", "slug", "name_es", "name_en" } ],
  "artworks": [
    {
      "id", "slug", "title_es", "title_en",
      "image", "image_alt_es", "image_alt_en",
      "artist_id", "year", "dimensions",
      "price_mxn", "price_usd",
      "disciplines": [ids], "techniques": [ids], "themes": [ids],
      "formats": [ids], "scales": [ids]
    }
  ]
}
```

Artwork items carry only ids into its ref lists; names live once in the top-level maps. The client builds `id -> name` lookups and treats availability as set membership. Artist entries carry `location_id`, dereferenced against the top-level `locations` list (itself bilingual like the taxonomies).

Value types are explicit: `id`, `artist_id`, `year` and taxonomy id arrays are integers; `price_mxn`/`price_usd` are JSON numbers (floats, decimal_places=2); every text field (`slug`, `name_*`, `title_*`, `image_alt_*`, `image`) is a string or `null`; `generated_at` is an ISO-8601 UTC timestamp ending in `Z`.

- **Alternative considered:** nesting full taxonomy objects inside each artwork — heavy duplication, larger payload. Rejected. The same reasoning applies to locations: instead of repeating location objects per artwork or per artist, one top-level `locations` list keeps the payload flat and minimal.

### D4 — Route-level `AllowAny` + no pagination

Per-view `permission_classes` and `pagination_class` overrides of the global settings. This is the only public route; everything else keeps `IsAuthenticated`. No build token: the data is inherently public (names, prices, buyable status), and a secret would only gate a public resource while adding build-env fragility.

### D5 — Server filters to buyable only

Queryset: `Artwork.objects.filter(is_active=True, status=ArtworkStatus.AVAILABLE)`, mirroring the existing `Artist.available_artworks` property so the rule lives in one place conceptually.

- **Alternative considered:** returning all active works with `status` and letting the client filter — rejected, ships dead data and risks stale client logic.

### D6 — Dual-language payload, one fetch

`es`/`en` values emitted side by side (`title_es`, `title_en`, …) so the single build renders both `/es` and `/en` routes from one fetch.

- **Alternative considered:** `?lang=` per-locale fetches doubling the build fetch. Rejected.

### D7 — One primary image per artwork

Take `images.filter(is_primary=True).first()`, falling back to the first image by `sort_order`. Cards need one URL. Alt text comes from the image's `alt_es`/`alt_en` fields, with an es-first fallback to the artwork title (mirroring the `translated_name` convention): `image_alt_es` prefers the image's `alt_es`, `image_alt_en` the image's `alt_en`, each falling back to the corresponding translated title.

### D8 — Implementation

- **Files:** `artworks/serializers.py` (new), `artworks/views.py` (one `CatalogAPIView`), `project/urls.py` (register `/api/catalog/`).
- **Performance:** `prefetch_related` the five M2Ms, `translations`, and `images`, plus `select_related("artist", "artist__location")` — one query pattern, flat at build time even at thousands of pieces. Locations reference data comes from the same `artist__location` select_related chain (deduped).
- **Testing:** DRF `APITestCase` with the fixture catalog; assert `AllowAny` (no auth header succeeds), available-only scoping (sold/reserved/on_loan excluded), stable payload keys, non-empty id arrays, and both languages present.

## Risks / Trade-offs

- **Shape coupling to the frontend** → the payload is a contract; break it and the SSG build silently mistranslates. Mitigation: D2's versioned-path convention + contract asserted by tests (key names and types).
- **Freshness depends on manual/on-push rebuild** → data can lag after edits. Accepted consciously; no cross-repo automation in scope.
- **Future second consumer forces refactor** → generic viewsets would replace this APIView; the serializer's flat output maps cleanly, keeping the refactor cheap. Deferred by YAGNI.
- **Large catalog bloat** → mitigated by minimal flat payload (≈300 B/artwork); at tens-of-thousands scale revisit with a faceted-search backend. Out of current bounds.

## Migration Plan

- Additive change: new route, no data migration, no change to existing endpoints.
- Deploy order: merge → run tests → deploy backend; frontend fetches the new endpoint on its next build. Older frontend builds remain valid (no removed routes).
- Rollback: revert the route registration/serializer; the frontend falls back to a previously built page until its next rebuild.