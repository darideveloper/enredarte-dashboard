## Context

The `artworks` app exists but has zero models. The project needs a bilingual (ES/EN) data layer for an artwork store catalog, consumed by an SSG frontend. We're building the foundation now; sales/commission modules come later.

## Goals / Non-Goals

**Goals:**
- Define `core` app with reusable abstract base models
- Define all domain models in `artworks` app: Artist, ArtCurator, Gallery, Artwork, taxonomy, media
- Bilingual text via per-model translation tables, not JSON or third-party packages
- Person fields (name, email, website, photo) shared via abstract `Person` base
- M2M between Artwork and Gallery with sort order through table
- Proper `on_delete` semantics, related_names, and nullability

**Non-Goals:**
- API endpoints (future change)
- Admin registration (future change — not included in this change)
- Sales/commission/order models (future change)
- Image processing/resizing (can be added later)

## Decisions

| Decision | Choice | Alternatives Considered |
|----------|--------|------------------------|
| Translation approach | Per-model Translation table (FK + language) | JSONField (no DB validation), `_es`/`_en` fields (schema changes per field addition), django-modeltranslation (magic) |
| Person handling | Abstract base class | Concrete multi-table inheritance (JOIN overhead), mixin (no shared defaults) |
| Gallery ↔ Artwork | M2M with explicit `ArtworkGallery` through table | Simple M2M (no sort_order), FK (one section only) |
| Taxonomy models | Own models with translations | CharField choices (not extensible via admin) |
| Price | Two Decimal fields (MXN + USD) | Single field + currency enum, JSON (no DB validation) |
| `on_delete` semantics | `PROTECT` for artist and taxonomy FKs on Artwork, `SET_NULL` for optional curator FK on Gallery, `CASCADE` for owned data (translations, images, ArtworkGallery) | — |
| Images | `ArtworkImage` model with `is_primary` and per-image alt text | Single image field on Artwork (no gallery), JSON array in Artwork (no queryability) |
| Slugs | Unique per model on `BaseModel` | Scoped per parent (unnecessary complexity for SSG) |

## Translation Pattern

Every translatable model follows this convention:

```python
class ArtworkTranslation(TranslationBase):
    artwork = models.ForeignKey(Artwork, on_delete=CASCADE, related_name="translations")
    language = models.CharField(max_length=5, choices=settings.LANGUAGES)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    class Meta:
        unique_together = [("artwork", "language")]
```

The main model stores non-translatable fields; the `Translation` table stores language-dependent text. SSG fetches `?language=es` or includes translations as nested array.

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Translation table JOINs could slow queries | Add `select_related`/`prefetch_related` in views; SSG fetches at build time, not runtime |
| Per-model translation tables = many tables | Schema is explicit and queryable; consider a `TranslatedField` descriptor for ergonomic `obj.title_es` access later |
| `Person` abstract means Artist and Curator each reproduce name/email/website columns | Acceptable — no JOIN overhead, and they're genuinely separate entities (different relationships, different future logic) |
| No exhibitions model yet | Covered by Gallery M2M + sort_order; a future Exhibition model can sit alongside it if needed |
