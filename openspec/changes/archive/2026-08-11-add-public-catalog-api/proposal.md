## Why

The SSG frontend (a separate Astro, single-build project) shows the catalog with artists + taxonomy faceted filters, where options that cannot yield results with the current selection are disabled. It fetches all buyable artworks in one call at build time, but this backend exposes no such endpoint: `artworks/views.py` is empty and the DRF router registers nothing. DRF's global defaults (`IsAuthenticated`, paginated 12/page) would also break a public build-time fetch.

## What Changes

- Add a public `GET /api/catalog/` endpoint returning, in a single response, the full catalogue needed by the SSG build: buyable artworks, the artist list, the location list, and all five taxonomy lists (discipline, technique, theme, format, scale), with names in both `es` and `en`.
- Scope the queryset to `is_active=True` and `status=AVAILABLE` (only buyable pieces).
- Ship each artwork denormalized and minimal: primary image URL, bilingual alt text, artist id, taxonomy ids as arrays — the exact shape the frontend's client-side facet logic consumes.
- Override DRF's global `IsAuthenticated` and pagination for this route only (`AllowAny`, no pagination).
- Add a `project/pagination.py` only if absent is **not** in scope — this change does not touch existing DRF config beyond the single route override.
- Provide backend tests covering the payload shape, available-only filter, auth bypass, and response stability.

## Capabilities

### New Capabilities

- `public-catalog-api`: Public, unpaginated `GET /api/catalog/` endpoint returning buyable artworks plus artist, location, and taxonomy reference lists (es/en) for the SSG build.

### Modified Capabilities

- None.

## Impact

- **Code**: `artworks/views.py`, new `artworks/serializers.py`, `project/urls.py` (register the catalog route), possibly `artworks/tests.py`.
- **API surface**: new public route `/api/catalog/`; no existing routes change.
- **Permissions**: this route bypasses the global `IsAuthenticated`; all other API endpoints keep current behavior.
- **Frontend contract**: payload shape is the source of truth for the Astro gallery page. Filename/location of the payload is defined in `design.md`.
- **Accessibility consistency**: buyable-status rule mirrors the existing `Artist.available_artworks` property.