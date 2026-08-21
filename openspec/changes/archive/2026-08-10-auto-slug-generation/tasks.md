## 1. Shared core infrastructure

- [x] 1.1 Add `unique_slugify(base, queryset)` helper in `core/models.py` (slugify + `-N` suffix loop) and expose it for reuse
- [x] 1.2 Change `BaseModel.slug` to `blank=True` (keep `unique=True`, `max_length=200`, `verbose_name="Slug"`) in `core/models.py`
- [x] 1.3 Add abstract `SlugBackfillMixin` in `core/models.py` with `slug_source = "name"` and a `build_slug_base()` hook, overriding `save()` to backfill the parent slug via `unique_slugify` when empty and the ES translation exists
- [x] 1.4 Generate and apply the migration for the `blank=True` change (`makemigrations` + `migrate`)

## 2. Wire up translation models

- [x] 2.1 Apply `SlugBackfillMixin` to `LocationTranslation`, `GalleryTranslation`, `DisciplineTranslation`, `TechniqueTranslation`, `ThemeTranslation`, `FormatTranslation`, `ScaleTranslation` in `artworks/models.py` (slug from ES `name`)
- [x] 2.2 Apply `SlugBackfillMixin` to `ArtworkTranslation` and override `build_slug_base()` to return `{artist.slug}-{title}` from the ES title

## 3. Token slugs for inline-only models

- [x] 3.1 Add a `save()` override to `ArtworkGallery` generating `unique_slugify(uuid4().hex[:12], ArtworkGallery.objects.all())` when `slug` is empty
- [x] 3.2 Add a `save()` override to `ArtworkImage` generating `unique_slugify(uuid4().hex[:12], ArtworkImage.objects.all())` when `slug` is empty

## 4. Refactor ArtistSocialLink to the shared helper

- [x] 4.1 Replace the inline uniqueness loop in `ArtistSocialLink.save()` with the shared `unique_slugify` helper (behavior unchanged)

## 5. Tests

- [x] 5.1 Add tests for `unique_slugify` (no collision, suffix on collision, slugified input)
- [x] 5.2 Add tests for `SlugBackfillMixin` (admin/ORM creation backfills from ES name, collision suffix, ES-missing no-op, existing slug preserved)
- [x] 5.3 Add tests for `ArtworkTranslation` composite slug (`{artist.slug}-{title}`, cross-artist distinctness, same-artist collision)
- [x] 5.4 Add tests for `ArtworkGallery`/`ArtworkImage` token slug generation (single and multiple inline rows, uniqueness)
- [x] 5.5 Confirm existing `ArtistSocialLink` slug tests (`test_create_link_autofills_slug`, `test_slug_unique_with_suffix`) still pass
- [x] 5.6 Run the full test suite and verify fixture commands (`base_loaddata`, `seed_loaddata`) still pass
