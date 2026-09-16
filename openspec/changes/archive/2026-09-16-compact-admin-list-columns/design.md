## Context

`ArtistAdmin.list_display` has 11 columns and `ArtworkAdmin.list_display` has 9 (`artworks/admin.py:385,982`). On a wide monitor both overflow, hiding the triage state (Artist: `display_active` + `subscription_status_badge` at positions 10–11; Artwork: `status` + `display_active` at 6 and 9). Exploration with the operator confirmed: years are detail-only, only Obras/Disponibles/Galerías counters are scanned, `views_count` is filter-only, taxonomy text can truncate, full price stays.

## Goals / Non-Goals

**Goals:**
- Status-first column order in both changelists with zero query impact.
- Narrow Artist to 7 and Artwork to 8 columns so a wide monitor shows triage state without horizontal scroll.
- Keep dropped data reachable (form Resumen, filters, detail page).

**Non-Goals:**
- No queryset/annotation changes (`get_queryset` stays as-is; unused annotations are cheap and keep Resumen working).
- No Unfold theme/table config, no responsive overhaul, no model/filter/search changes.
- No price-format or badge redesign.

## Decisions

1. **Reorder `list_display` only, in place.** Artist → `display_name, display_email, display_active, subscription_status_badge, display_artworks_count, display_available_count, display_galleries_count`. Artwork → `display_image, display_title, status, display_active, artist, display_taxonomies, display_price, is_highlighted`. Rationale: single-list edit, order-safe tests (`assertIn`), sorting/`ordering` attrs untouched. Alternative (custom `display_*` merged columns, e.g. "Obras 12 (3 disp.)") rejected — breaks sorting, YAGNI.
2. **Drop, don't merge.** Remove `birth_year`, `death_year`, `display_techniques_count`, `display_highlighted_count` (Artist) and `views_count` (Artwork) from `list_display` only. Rationale: biggest width win for zero logic; data stays in form/filters/Resumen. Alternative (single combined year/counter column) rejected per operator answer "detail page is enough".
3. **Truncate `display_taxonomies` to ~60 chars + ellipsis in the list.** Full joined string stays on the change form (no method split; truncate at render end, e.g. `text[:57] + "..."` when longer). Rationale: this is the widest Artwork column (5 axes joined); truncation is presentation-only. Alternative (reduce to 2 axes) rejected — loses signal; truncation keeps all axes visible on hover/detail. Add a `title` attribute with the full untruncated text so the complete summary stays reachable on hover.
4. **Keep `get_queryset` annotations untouched** (including `_techniques_count`, `_highlighted_count`). Rationale: Resumen fieldset and future re-adds reuse them; `Count` annotations cost one row per artist regardless.

## Risks / Trade-offs

- [Risk] Operator misses a dropped column (e.g. Técnicas count in list) → Mitigation: still in Resumen fieldset + reachable in 1 click; spec deltas document the move.
- [Risk] Truncated taxonomy hides a distinguishing term → Mitigation: 60-char budget covers 1–2 axes; full text on change form; title-attr tooltip if trivial.
- [Risk] Prose/docs listing old column order drift → Mitigation: delta specs update the two affected requirements; no other docs reference order.
