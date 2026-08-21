## Why

The client catalog requires filtering artworks by five dimensions — disciplina, técnica, temática, formato, and artista — but the current data model only covers three (Category, Medium, Surface) and cannot represent the client's actual values. The catalog's filter structure must match the client's taxonomy so the editor can correctly classify and later browse/filter every artwork.

## What Changes

**BREAKING** — Model restructure in `artworks/models.py` (no data exists yet, so old taxonomy tables are dropped and fresh ones created):

- Remove `Category`, `Medium`, `Surface` (and their translation models) and the `category`/`medium`/`surface` FKs on `Artwork`.
- Replace them with five ManyToMany fields:
  - `disciplines` (→ `Discipline`)
  - `techniques` (→ `Technique`)
  - `themes` (→ `Theme`, new)
  - `formats` (→ `Format`, new — "tipo de pieza")
  - `scales` (→ `Scale`, new — "tamaño")
- `Artwork.artist` stays a single FK ("por artista"); all five taxonomy axes are multi-select.
- Add translatable models `Discipline`, `Technique`, `Theme`, `Format`, `Scale`, each with an `<X>Translation` (`BaseModel` + `TranslationBase` pattern, es/en, `unique_together`).
- Add 36 bilingual base rows via **fixtures** (`docs/django-fixtures.md` pattern): 6 disciplinas, 7 técnicas, 15 temáticas, 6 formatos, 2 escalas, with one JSON file per model (row + translation files) and fixed PK/slug identities recorded in the `artwork-taxonomies` spec.
- Add **seed fixtures** with random demo data (`artworks/fixtures/artworks/seed/`): 3–5 sample artists and a few sample artworks wiring arbitrary taxonomy combinations — loaded once per environment via `seed_loaddata`.
- Add fixture loader commands `base_loaddata` / `seed_loaddata` in `core/management/commands/` (auto-discover all apps, fail-soft), `FIXTURE_DIRS`, and invoke `base_loaddata` in the Dockerfile build, `start.sh`, and tests.
- Update the Artwork admin: register the new taxonomy admins (Discipline, Technique, Theme, Format, Scale) each with bilingual inlines, `filter_horizontal` M2M widgets, updated fieldsets/list_filters/list_display, Spanish client-term labels (Disciplina · Técnica · Temática · Tipo de pieza · Tamaño), and unregister Surface.
- Update `artworks/tests.py` for the new taxonomy models, M2M creation, new admins, removed `Surface`, and base-fixture loading in `setUp`.

## Capabilities

### New Capabilities
- `artwork-taxonomies`: The five artwork taxonomy axes (Discipline, Technique, Theme, Format, Scale) as translatable, admin-manageable, fixture-seeded models wired to `Artwork` as ManyToMany relations, plus random demo data as seed fixtures.
- `fixture-loading`: The `base_loaddata`/`seed_loaddata` commands that auto-discover and load base/seed fixture JSON from every installed app, per `docs/django-fixtures.md`.

### Modified Capabilities
- `artwork-admin`: Artwork admin form gains the five ManyToMany taxonomy fields (filter_horizontal widgets), new list filters, updated fieldsets/list columns, and Spanish taxonomy labels; `Surface` admin is removed; `Category`/`Medium` admin become `Discipline`/`Technique`.

## Impact

- **Code**: `artworks/models.py`, `artworks/admin.py`, `artworks/tests.py`, `artworks/migrations/0002_...`, `core/management/commands/base_loaddata.py`, `core/management/commands/seed_loaddata.py`, `project/settings.py` (`FIXTURE_DIRS`), `Dockerfile`, `start.sh` (base_loaddata step).
- **New files**: `artworks/fixtures/artworks/` JSON fixtures per model (`Discipline`, `DisciplineTranslation`, `Technique`, `TechniqueTranslation`, `Theme`, `ThemeTranslation`, `Format`, `FormatTranslation`, `Scale`, `ScaleTranslation`) and `artworks/fixtures/artworks/seed/{Artist,ArtistTranslation,Artwork,ArtworkTranslation}.json`.
- **Data**: DB is empty today — `Category`/`Medium`/`Surface` tables are dropped and fresh taxonomy tables created. Taxonomy values seeded via base fixtures; demo artists/artworks seeded via `seed_loaddata` (run once).
- **Docs**: leveraged `docs/django-fixtures.md` pattern (no changes needed to that doc itself).
- **Out of scope**: public/API rendering of the filters, gallery/curator logic, artwork pricing/status.