## Context

`sort_order` is defined on the abstract `BaseModel` (`core/models.py:29`), which every domain model in the `artworks` app inherits. Today 11 concrete models carry the column, admin field, serializer field, and fixture value, but only two models genuinely use it to order content: `ArtworkGallery` (join table between artwork and gallery) and `ArtworkImage` (ordered gallery of a work's images). Both already declare `sort_order` as a *local* field (`artworks/models.py:293` and `:313`), so the inherited copy is redundant for them and pure dead weight everywhere else.

This change is a simplification: the field stays exactly where it is used, and is removed everywhere it is not.

## Goals / Non-Goals

**Goals:**
- Remove `sort_order` from the abstract `BaseModel` and from all 11 models that only inherited it.
- Drop the DB columns via a single new migration.
- Clean every surface that exposes the removed field: Django Admin (fieldsets, `list_display`, auto-fill initial-data, `Max` aggregates), REST serializers, Bruno examples, fixtures, tests, and the affected live openspec specs.
- Keep `sort_order` fully intact on `ArtworkGallery` and `ArtworkImage`, including `Meta.ordering` and admin inline drag-and-drop.
- Give every queryset that previously ordered by `sort_order` a deterministic replacement ordering.

**Non-Goals:**
- Removing `sort_order` from `ArtworkGallery` / `ArtworkImage` (they are the reason the field survives).
- Removing the other `BaseModel` fields (`slug`, `is_active`) or `TimeStampedModel` timestamps.
- Renaming `sort_order` to a different field name.
- Touching archived openspec changes.

## Decisions

**D1 — Remove the field from the abstract `BaseModel` (not per-model).**
One line deleted in `core/models.py` removes the column from all 11 inheriting models at once, since each concrete model materializes its own column from the abstract base. Kept the `TranslatableName` docstring in sync.
*Alternative rejected:* keeping `sort_order` on `BaseModel` and excluding it per model (`exclude` in `_meta` / admin `exclude` lists) — leaves the columns in the DB and requires 11 separate exclusions; more code, more room for error, no benefit.

**D2 — `ArtworkGallery` / `ArtworkImage` need no model change.**
They already declare `sort_order` locally, so removing it from `BaseModel` leaves their schemas unchanged. Their `Meta.ordering = ["sort_order"]` and admin `ordering_field` stay as-is.

**D3 — One new migration with 11 `RemoveField` operations.**
Django will autogenerate `artworks/0007_*` dropping the column for `artist`, `artcurator`, `artistsociallink`, `location`, `gallery`, `discipline`, `technique`, `theme`, `format`, `scale`, `artwork`. No data migration is needed — the dropped values are unused everywhere.
*Alternative rejected:* editing/amalgamating the six historical migrations (`0001`–`0006`) so the columns never exist. Migrations are immutable history; rewriting them breaks any deployed database and is far riskier than a forward migration.

**D4 — Replace `order_by("sort_order")` with `order_by("-created_at")`.**
Applied to all six viewset querysets in `artworks/views.py` and to `Artist.techniques`, `Artist.available_artworks`, and `Artist.highlighted_artworks` in `artworks/models.py`. `created_at` is `db_index=True` (set in `0005`), so ordering is cheap and deterministic. Newest-first is the sensible catalog default.
*Alternatives considered:* `id` ordering — stable but conveys no meaning for a public catalog; no explicit ordering — nondeterministic across databases; `translations__name` ordering for techniques — mixes languages and adds joins for no user-facing gain.

**D5 — Remove the `get_changeform_initial_data` auto-fill in admin.**
All 10 admin classes that override it (`ArtistAdmin`, `ArtCuratorAdmin`, five taxonomy admins, `LocationAdmin`, `GalleryAdmin`, `ArtworkAdmin`) lose the method, the `Max("sort_order")` aggregate, and the `sort_order` entries in `fieldsets` / `list_display`. `Max` is dropped from the `django.db.models` import. The three inlines on models that keep the field (`ArtworkGalleryInline`, `GalleryArtworkInline`, `ArtworkImageInline`) keep `ordering_field = "sort_order"`; `ArtistSocialLinkInline` loses it.

**D6 — Fixtures are cleaned in the same change, not deferred.**
`loaddata` (invoked by `base_loaddata`/`seed_loaddata` in `start.sh`, the Dockerfile, and tests) raises a `DeserializationError` when a fixture supplies a field the model no longer has. Removing `sort_order` from the 11 affected fixture files is therefore a hard requirement of this change, not a follow-up. The `seed/08_ArtworkGallery.json` and `seed/09_ArtworkImage.json` fixtures keep `sort_order`.

**D7 — API-facing removals are intentional and documented as breaking.**
`sort_order` is dropped from `ArtistSerializer`, `ArtCuratorSerializer`, `LocationSerializer`, `GallerySerializer`, `_TaxonomySerializer`, and `ArtworkSerializer` top-level payloads, and from the matching Bruno examples. It remains on `ArtworkImageSerializer` and the two `ArtworkGallery` link serializers. The delta specs record the contract change so consumers can adapt.

## Risks / Trade-offs

- **BREAKING API response shape** → The removal is the point of the change. It is captured in the `artworks-rest-api` delta spec so frontend consumers can drop `sort_order` reads in the same release. No compatibility shim is added (YAGNI).
- **A fixture row missed keeps `sort_order` and `loaddata` fails** → All 11 fixture files are edited in this change and the change is verified by running the fixture-loading test suite (`ArtworkAdminTestCase.setUp` calls `base_loaddata`).
- **Admin list/display ordering changes for affected models** → Explicit `-created_at` ordering replaces the old `sort_order` order, so the change is deterministic rather than accidental.
- **Deleting `get_changeform_initial_data` changes add-form behavior** → The field it populated no longer exists; the method is dead code after the removal. Deleting it is safe and verified by the admin render tests.

## Migration Plan

- **Apply:** Commit code + migration together. Run `makemigrations` to generate `artworks/0007_*`, then `migrate`. No data transformation step.
- **Verify:** `python manage.py makemigrations --check --dry-run` shows no pending changes; run the test suite (admin, fixtures, API) and `manage.py loaddata` of all fixture files.
- **Rollback:** `migrate artworks 0006` restores the columns (with `default=0`), and the prior commit's code is redeployed. No data is lost by the forward migration since the columns were unused.

## Open Questions

None — the two decisions that shape this change were settled in the proposal phase: replacement ordering is `-created_at`, and `sort_order` is kept only on `ArtworkGallery`/`ArtworkImage`.