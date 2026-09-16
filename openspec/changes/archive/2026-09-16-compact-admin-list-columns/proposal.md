## Why

The Artist (11 columns) and Artwork (9 columns) changelists always overflow horizontally on a wide monitor, pushing the most-scanned state — active/subscription for artists, status/active for artworks — off-screen. Reordering status first and trimming rarely-scanned columns makes the daily triage ("who can sell? what is sellable?") visible without scrolling.

## What Changes

- **Artist (`ArtistAdmin.list_display`, `artworks/admin.py:385`)**: reorder to `display_name, display_email, display_active, subscription_status_badge, display_artworks_count, display_available_count, display_galleries_count`. Drop `birth_year`, `death_year` (detail page only), `display_techniques_count`, `display_highlighted_count` (stay in Resumen fieldset + annotated queryset, just not columns).
- **Artwork (`ArtworkAdmin.list_display`, `artworks/admin.py:982`)**: reorder to `display_image, display_title, status, display_active, artist, display_taxonomies, display_price, is_highlighted`. Drop `views_count` from columns (keep filter + form). Truncate `display_taxonomies` to ~60 chars with ellipsis in the list (full detail stays on the change form).
- No queryset, annotation, filter, search, or model changes. No migrations.

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `artist-admin`: changelist column set and order change (status before counters; years + 2 counters removed from list).
- `artwork-admin`: changelist column order change (status/active after title; views_count removed from list; taxonomy summary truncated in list).

## Impact

- Affected code: `artworks/admin.py` only (`ArtistAdmin.list_display`, `ArtworkAdmin.list_display`, `display_taxonomies` truncation).
- Specs: delta specs for `artist-admin` and `artwork-admin`.
- Tests: existing `artworks/tests.py` uses `assertIn` on `list_display` (order-safe); add/adjust order assertions for the new column sequence.
- No API, fixture, Stripe, or DB impact.
