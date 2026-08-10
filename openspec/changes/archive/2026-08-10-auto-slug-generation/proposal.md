## Why

Most models in this project require a manually typed, unique `slug`, even though their display name (or a natural composite) is already entered elsewhere. Only `Artist`, `ArtCurator` (admin `prepopulated_fields`) and `ArtistSocialLink` (a `save()` override) get auto-filled. The rest — every translated model plus `ArtworkGallery`/`ArtworkImage` — demand manual entry or break: the inline-only models (`ArtworkGallery`, `ArtworkImage`) exclude `slug` from their inline forms entirely, so creating a second row per object violates the UNIQUE constraint on empty strings. This change makes slug generation automatic, consistent, and DRY across all models.

## What Changes

- `BaseModel.slug` becomes `blank=True` so auto-generation can run after form validation (migration required, no DB column change).
- A shared, reusable `unique_slugify(base, queryset)` helper centralizes the "append `-1`, `-2`, … on collision" logic currently copied in `ArtistSocialLink.save()`.
- A shared abstract `SlugBackfillMixin` (a `save()` override, following Django's documented pattern and the existing `ArtistSocialLink` precedent) backfills the parent's slug from the ES translation when empty. Applied to the 8 translation models:
  - `Location`, `Gallery`, `Discipline`, `Technique`, `Theme`, `Format`, `Scale`: slug = ES `name`.
  - `ArtworkTranslation`: slug = `{artist.slug}-{title}` (e.g. `frida-kahlo-las-dos-fridas`).
- `ArtworkGallery` and `ArtworkImage` auto-generate a unique random token slug via `save()` (their slugs are meaningless internal identifiers, and their inline forms hide the field).
- Existing behavior is preserved: `Artist`/`ArtCurator` keep `prepopulated_fields`, `ArtistSocialLink` keeps its `save()` override; auto-generation only fills the slug when it is empty and never overwrites a user-provided value.

## Capabilities

### New Capabilities
- `slug-auto-generation`: automatic, DRY slug generation for all slug-bearing models — translation-derived slugs via a shared backfill mixin, token slugs for inline-only relation/image models, and a shared uniqueness helper.

### Modified Capabilities
- `artist-social-links`: `ArtistSocialLink` slug generation is refactored to use the shared `unique_slugify` helper (behavior unchanged).

## Impact

- **Code**:
  - `core/models.py` — `BaseModel.slug` `blank=True`; new `SlugBackfillMixin` abstract model; `unique_slugify` helper.
  - `artworks/models.py` — 8 translation classes inherit the mixin; `ArtworkTranslation` overrides the slug base; `ArtworkGallery`/`ArtworkImage` add `save()` token generation; `ArtistSocialLink.save()` uses the shared helper.
  - `artworks/admin.py` — no functional change required (slug stays hidden in inlines; admin keeps working via backend generation).
- **Database**: one migration (`AlterField` slug → `blank=True`, `max_length=200`, `unique=True`); no schema/data change.
- **Fixtures**: unaffected — fixture rows carry explicit slugs, and backfill only runs when the slug is empty.
- **Tests**: new tests for mixin backfill, artwork composite slug, token generation, and uniqueness suffixes.
