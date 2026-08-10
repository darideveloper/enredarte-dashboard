# Design: Auto Slug Generation

## Context

All slug-bearing models inherit `slug = models.SlugField(max_length=200, unique=True)` from `BaseModel` (`core/models.py:14`). Currently only three models have any slug automation:

- `Artist` / `ArtCurator` — admin `prepopulated_fields = {"slug": ("name",)}` (`artworks/admin.py:188`, `:335`), because `name` is a real column on them.
- `ArtistSocialLink` — a `save()` override (`artworks/models.py:80-89`) that builds `{artist.slug}-{platform}` with a manual uniqueness suffix loop.

The other 10 slug-bearing models have **no** automation. 8 of them (`Location`, `Gallery`, `Discipline`, `Technique`, `Theme`, `Format`, `Scale`, `Artwork`) keep their display name in a required `*Translation` row (ES/EN enforced by `TranslationInlineFormSet`, `artworks/admin.py:40-67`); `ArtworkGallery` and `ArtworkImage` are created only via admin inlines that exclude the `slug` field (`admin.py:142`, `:632`), so a second row per parent violates the UNIQUE constraint on the empty-string default.

Key structural fact: **Django admin saves the parent before its inline formsets** (`save_model` → `save_formset`). A parent-side `save()`/`pre_save` cannot see the ES translation on first creation.

## Goals / Non-Goals

**Goals:**
- Every slug-bearing model gets automatic slug generation, with no manual entry.
- One DRY implementation shared across models (single helper + single mixin).
- Generation only fires when the slug is empty; never overwrites user data.
- Works identically via admin and ORM creation paths.

**Non-Goals:**
- No public URL routing / SEO work (no views consume slugs yet).
- No change to `Artist`/`ArtCurator` admin `prepopulated_fields` behavior.
- No data migration to backfill existing empty slugs (fixtures already provide slugs).
- No refactor of `BaseModel` inheritance for `ArtworkGallery`/`ArtworkImage` (they keep `is_active`/`sort_order`).

## Decisions

### Decision 1: Backfill on the translation model, not the parent

**Chosen:** An abstract `SlugBackfillMixin` overrides `save()` on each `*Translation` model: `super().save()`, then if `parent.slug` is empty, set it from the ES translation and save the parent.

**Rationale:** The translation row is saved *after* the parent exists, so `parent.pk` and the ES `name`/`title` are both available at the exact right moment. This single mechanism covers admin creation, ORM creation, and edits uniformly. It follows Django's documented pattern for slug generation (override `save()`), matches the existing `ArtistSocialLink` precedent, and needs no `apps.py` wiring.

**Alternatives considered:**
- `post_save` signal on translation models — functionally identical timing, but implicit ("magic"), requires `apps.ready()` wiring plus a `raw` guard for fixture loading; rejected as a worse fit for an already-explicit codebase.
- Parent-side `save()` override — cannot read translations during admin first-create (parent saved first); rejected as sole mechanism.
- Admin `save_model`/formset override — works but is admin-only and duplicates logic across 8 admin classes; rejected.

### Decision 2: `BaseModel.slug` becomes `blank=True`

**Chosen:** Change `slug = models.SlugField(max_length=200, unique=True, blank=True, verbose_name="Slug")` (migration: `AlterField`, no DB column change).

**Rationale:** With `blank=False` the parent form rejects the empty slug during validation, before any generation can run. `blank=True` is the standard Django pattern for auto-generated-but-editable slugs; it is harmless for `Artist`/`ArtCurator` (prepopulated) and `ArtistSocialLink` (save override).

### Decision 3: Shared `unique_slugify(base, queryset)` helper

**Chosen:** Extract the uniqueness loop from `ArtistSocialLink.save()` into `unique_slugify` in `core/models.py` and reuse it in the mixin, the token generation, and `ArtistSocialLink.save()` itself.

**Rationale:** Three call sites need the same "append `-N` until unique" behavior; one helper guarantees consistent, DRY behavior and is directly unit-testable.

### Decision 4: Token slugs for `ArtworkGallery` / `ArtworkImage`

**Chosen:** Add a `save()` override to each that, when `slug` is empty, sets `self.slug = unique_slugify(uuid4().hex[:12], <model>.objects.all())`.

**Rationale:** These rows' slugs are meaningless internal identifiers (hidden from admin inlines). A random token avoids manual entry, avoids UNIQUE collisions on empty strings, and requires no schema change. Mirrors the `ArtistSocialLink` pattern.

### Decision 5: Per-class slug base via a hook

**Chosen:** `SlugBackfillMixin` exposes `slug_source = "name"` and a `build_slug_base()` method. The 7 simple translations inherit the default (ES `name`); `ArtworkTranslation` overrides `build_slug_base()` to return `f"{self.artwork.artist.slug}-{self.title}"`.

**Rationale:** Keeps the mixin DRY while allowing the one composite case (Artwork) without branching logic in the mixin.

## Risks / Trade-offs

- **Double write on admin create** → Parent saves with empty slug, then the ES translation save triggers a second parent `UPDATE`. Two writes per creation; acceptable at admin data volumes.
- **Transient empty slug + UNIQUE race** → Two concurrent creates could both hold `slug=""` between parent save and translation save. Not reachable through serialized admin requests (each request completes its translations before the next); accepted and documented, not engineered around.
- **`bulk_create` bypasses `save()`** → No backfill for bulk translation inserts. `bulk_create` is not used for translations in this repo; if introduced later, fixtures/scripts must supply slugs.
- **ES translation missing leaves empty slug** → The mixin no-ops instead of guessing, per spec; the admin formset already enforces ES+EN presence, so this is unreachable through the admin.
- **Migration surface** → `AlterField` on `BaseModel` touches every concrete table's model definition but only flips a Python-level flag; no column change, trivially reversible.

## Migration Plan

1. Apply the `AlterField` migration (`makemigrations` + `migrate`).
2. Run the test suite; add/adjust tests per `tasks.md`.
3. Verify fixture loading (`base_loaddata`, `seed_loaddata`) still passes.
4. Manual smoke test: create one `Discipline`, one `Artwork`, and multiple `ArtworkImage` rows in the admin; confirm slugs appear automatically.

**Rollback:** Revert the `blank=True` on `BaseModel.slug` and the model mixins/save overrides; no data transformation is performed, so rollback is lossless.
