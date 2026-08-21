## Context

All concrete models inherit `BaseModel` (whose `__str__` returns `self.slug`) or `Person` (whose `__str__` returns `self.name`). Display names/titles for `Location`, `Gallery`, `Discipline`, `Technique`, `Theme`, `Format`, `Scale`, and `Artwork` live only in their `*Translation` rows (`language` in `settings.LANGUAGES = [("es", "Español"), ("en", "English")]`, `related_name="translations"`). Translation and join models (`ArtistSocialLink`, `ArtworkGallery`, `ArtworkImage`) currently fall back to slug or Django's default `"Model object (N)"`.

The admin already implements the "prefer es, fallback to any translation" lookup in 6 duplicated `display_name` methods plus `_translated_name`/`_artwork_title` (artworks/admin.py:260, 268). Django renders M2M widgets, related dropdowns, and FK columns through `__str__`, so the Artwork `filter_horizontal` widgets show slugs today.

## Goals / Non-Goals

**Goals:**
- Every concrete model returns a Spanish, content-based `__str__`.
- Reuse the existing "es-first, then any language, then slug" convention already established in the admin.
- Keep the diff minimal and Python-only (no migrations).

**Non-Goals:**
- Refactoring the admin `display_name`/`_translated_name`/`_artwork_title` helpers to reuse the new model methods (explicitly deferred; admin behavior and its `"-"` fallback are untouched).
- Performance optimization (prefetching/select_related) for `__str__` lookups.

## Decisions

**1. Shared abstract mixin `TranslatableName` in `core/models.py`** — for the 7 models whose translated field is `name`:

```python
class TranslatableName(BaseModel):
    class Meta:
        abstract = True

    def translated_name(self, language="es"):
        t = self.translations.filter(language=language).first() or self.translations.first()
        return t.name if t else self.slug

    def __str__(self):
        return self.translated_name()
```

Rationale: one definition instead of 7 near-identical copies. Alternative considered: adding the lookup to `BaseModel` — rejected because `Artist`/`ArtCurator` (bio-only translations), `Artwork` (`title` not `name`), and join models also inherit it and would break.

> Note: `TranslatableName` extends `BaseModel` (not `models.Model`) so the 7
> subclasses keep `slug`/`is_active`/`sort_order` (used by the admin
> `list_display`/`list_filter` and by `ArtistSocialLink.save`'s slug
> derivation). Replacing `BaseModel` with a plain `models.Model` mixin would
> drop those fields, require migrations, and break the admin — contradicting
> the proposal's "No migrations (Python-only change)" goal.

**2. `Artwork` gets its own `translated_title()`** using the same lookup on `title` (the only model whose translated field is not `name`). Kept on the class rather than generalized in the mixin to avoid a "field name" indirection for one use.

**3. Translation rows return `"{parent} ({language})"`** (e.g. `"Guadalajara (es)"`). Each of the 10 translation models defines a one-line `__str__` referencing its own FK field (`artist`, `location`, `art_curator`, `gallery`, `discipline`, `technique`, `theme`, `format`, `scale`, `artwork`). Parenthesized language makes rows unique and self-describing in inline admin contexts.

**4. Join models use Spanish content:**
- `ArtistSocialLink.__str__` = `f"{self.get_platform_display()} — {self.artist}"` (platform labels are already Spanish via `TextChoices`).
- `ArtworkGallery.__str__` = `f"{self.artwork} en {self.gallery}"` (unique due to `unique_together`).
- `ArtworkImage.__str__` = `self.alt_es or f"Imagen de {self.artwork}"`.

**5. `Artist`/`ArtCurator` unchanged** — `Person.__str__` already returns the name.

**6. Docs** — update `docs/django-i18n-es-admin.md` Step 2 to document the translated-model `__str__` convention (`TranslatableName` / `translated_name()` Spanish-first lookup) alongside the existing direct-`name` example.

## Risks / Trade-offs

- [N+1 queries] `__str__` now queries `translations`; the Artwork `filter_horizontal` widgets render ~36 taxonomy rows → ~36 queries per change page → Acceptable at current data scale; revisit prefetching only if the catalog grows or a profiler calls for it.
- [Mixin accidentally applied to a model without `translations`] → Mixin is only applied to the 7 models with a `name`-bearing `translations` relation; `translated_name` would raise on others, but no such application is being made.
- [Slug vs. `"-"` fallback divergence from admin] → Admin `display_name` still returns `"-"` when untranslated while `__str__` returns the slug; acceptable, and only visible in non-admin contexts. Deferred DRY refactor would unify this later.
