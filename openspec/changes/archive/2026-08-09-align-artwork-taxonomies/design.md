## Context

`Artwork` currently attaches to three single-value foreign keys (`category`, `medium`, `surface`) plus `artist`. The client requires five filter dimensions — **disciplina**, **técnica**, **temática**, **formato**, **artista** — where formato maps to two axes ("tipo de pieza" + "tamaño"). The existing `Category`/`Medium`/`Surface` taxonomy cannot hold the client's values (no temas, no formatos, and "Surface" is not requested). The bilingual (es/en) `BaseModel`/`TranslationBase` pattern is the established convention for taxonomy models in this repo, and `docs/django-fixtures.md` defines the fixture/loader pattern for reference data.

Constraints from the codebase:
- All taxonomy models follow `BaseModel` (slug, is_active, sort_order, timestamps) + `<X>Translation` (`TranslationBase`, `unique_together` on `(x, language)`).
- `settings.LANGUAGES = [("es", ...), ("en", ...)]` — translations are es+en.
- Django Admin uses Unfold (`ModelAdminUnfoldBase`) with bilingual inline helpers in `artworks/admin.py`.
- Database is SQLite by default; test DB via `IS_TESTING`.

## Goals / Non-Goals

**Goals:**
- Artworks filtered by the client's five dimensions, with all values seeded and bilingual.
- All primary taxonomies multi-select (matches the client's "por tema/por técnica" semantics).
- Surface removed entirely (no longer a filter).
- Base fixture data reloadable on every fresh environment via `base_loaddata`.

**Non-Goals:**
- No public/API/readeras rendering or filter endpoints — this change is model + admin + fixtures only.
- No changes to gallery/curator, pricing, status, or artist logic.

## Decisions

### 1. Every taxonomy axis as a `ManyToMany` on Artwork
`artworks.models.Artwork` grows `disciplines`, `techniques`, `themes`, `formats`, `scales` (all `related_name="artworks"`, `blank=True`). `Artist` remains a single FK.
**Alternative considered:** keep single FKs (like today) for discipline/technique/format/scale. Rejected: the client's catalog lets a piece belong to several topics (e.g. Feminismo + Memoria), and the user confirmed multi-select for **all** axes — uniform M2M keeps the admin consistent and future-proof.

### 2. Drop old taxonomies, create fresh (no data to preserve)
The database is empty (`Artwork`, `Category`, `Medium`, `Surface` all have zero rows). So rather than row-preserving renames, delete `Category`, `Medium`, `Surface` (+ translations) and add brand-new `Discipline` and `Technique` models with the exact class names the code wants. No data was at risk.
- Alternative: `RenameModel` `Category→Discipline`, `Medium→Technique`. Rejected: with zero rows it's pure ceremony; fresh models keep history clean (no orphaned `artworks_category` table names in migrations).
- `Surface` is not in the client's five dimensions → delete (confirmed with client).

### 3. Split "formato" into two axes: `Format` + `Scale`
Client list flattened into `Format` ("tipo de pieza"): Obra original, Edición limitada, Prints, Series, Esculturas, Objetos; and `Scale` ("tamaño"): Mini obras, Gran formato. Preserves all 8 client values while keeping the two mental models separable.
- Alternative: one `Format` FK with all 8. Rejected — user explicitly chose the split.

### 4. Fixtures (base tier) for all taxonomy values
Per `docs/django-fixtures.md`: one JSON per model at `artworks/fixtures/artworks/` with explicit PKs + es/en names. Rows are **base** (always loaded) because the catalog can't classify a piece without them.
- New loader commands `core/management/commands/base_loaddata.py` + `seed_loaddata.py` (auto-discover `<app>/fixtures/<app>/` and `<app>/fixtures/<app>/seed/`), fail-soft `try/except`, sorted load order. Following `docs/django-fixtures.md`, there is one JSON file **per model**: each taxonomy gets a `<Model>.json` plus a `<Model>Translation.json` (es + en rows referencing the row PK).
- `FIXTURE_DIRS` in `project/settings.py`; `base_loaddata` invoked in `start.sh` (the container runtime entrypoint, which the Dockerfile CMD runs) and test bootstrap. The Dockerfile build itself cannot load fixtures (no database at build time), so it carries a comment documenting the runtime load.
- The 36 values, their fixed PKs, and their un-accented kebab slugs are recorded as a shared manifest in `specs/artwork-taxonomies/spec.md`; fixtures, seeds, and tests all read from it.
- Alternative considered: hardcoded `TextChoices`. Rejected — user chose fixtures; DB rows keep the admin able to add future values without code changes.

### 5. Admin
- Register = same `ModelAdminUnfold` base + bilingual translation inline for `Discipline`, `Technique`, `Theme`, `Format`, `Scale`; unset/`Unregister(Surface)`.
- `ArtworkAdmin` uses `filter_horizontal` for the five M2M, updates the `fieldsets` (taxonomy group), list filters `["status", "is_active", "disciplines", "techniques", "themes", "formats", "scales"]`, `search_fields` referencing taxonomy translation names, and Spanish client-term labels (verbose_name on models: Disciplina, Técnica, Temática, Tipo de pieza, Tamaño).
- Mirror the existing per-model taxonomy admin pattern (slug + sort_order init) — the inline classes are per-model; each new taxonomy gets its own inline (can share a factory if straightforward, otherwise duplicating is acceptable — YAGNI on an abstraction).

### 6. Migration ordering (drop + add, no data step)
Because no rows exist, the migration `0002` is generated, not authored:
1. `DeleteModel` `Category`, `Medium`, `Surface` + their translation models.
2. `CreateModel` `Discipline`, `Technique`, `Theme`, `Format`, `Scale` + translations.
3. `RemoveField` `Artwork.category`/`medium`/`surface`.
4. `AddField` the five M2M (`disciplines`, `techniques`, `themes`, `formats`, `scales`).
- Runs as plain `makemigrations` + `migrate`; no data migration required.

### 7. Demo data as seed fixtures (random)
Seed tier `artworks/fixtures/artworks/seed/` holds random demo content: 3–5 `Artist` rows and a handful of `Artwork` rows referencing the base taxonomy PKs with varied discipline/technique/theme/format/scale combos and statuses. Loaded once per environment via `seed_loaddata` (never in the Docker build) per `docs/django-fixtures.md`. This lets the editor/admin see working filters immediately without hand-entering content.
- Alternative: hand-enter demo art in the admin. Rejected — fixtures make demo data repeatable and drop the seed-loadstep from the build pipeline.

## Risks / Trade-offs

- [Stale references to old field names in admin/tests after drop] → Landed in same pass; grep for `category`/`medium`/`surface` before merging.
- [`loaddata` duplicate-key failures when run again] → `base_loaddata` is for fresh builds only; fail-soft loop prints+skips, and `seed_loaddata` is "run once" by convention.
- [M2M bloat on artworks with many themes] → trivial at catalog scale; no indexing work needed.
- [Seeded demo artworks reference taxonomy PKs that change on re-seed] → seed row PKs are fixed in the fixtures; the fail-soft loop handles re-runs.

## Migration Plan

1. `python manage.py makemigrations` + `migrate` applies `artworks/migrations/0002_...` (drop old taxonomy models/FKs, create five new translatable models + M2M fields).
2. `python manage.py base_loaddata` seeds the 36 taxonomy rows (fresh environments; runs at container runtime via `start.sh` after `migrate`).
3. `python manage.py seed_loaddata` (once, per env, manual) loads the random demo artists/artworks.
4. Tests: `base_loaddata` in `setUp` where taxonomy values are required.
5. Rollback: `migrate artworks 0001` restores `Category`/`Medium`/`Surface` columns; new tables remain — a full reset is advisable on dev.

## Open Questions

- None blocking. (Confirmed: multi-select on all axes; drop old taxonomy tables and create new `Discipline`/`Technique`; split Format/Scale; delete Surface; bilingual fixtures; seed demo data with random values; slugs approved.)
- Note: keep the exact fixture slugs/pks recorded in the `artwork-taxonomies` spec so loader, seeds, and tests share one dependency graph.