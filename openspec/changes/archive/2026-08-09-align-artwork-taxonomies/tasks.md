## 1. Models

- [x] 1.1 Remove `Category`, `Medium`, and `Surface` models + their translations (`CategoryTranslation`, `MediumTranslation`, `SurfaceTranslation`) from `artworks/models.py`
- [x] 1.2 Add translatable `Discipline` and `Technique` models (replacing `Category`/`Medium`) with the standard `BaseModel` + `TranslationBase` pattern
- [x] 1.3 Add `Theme`, `Format`, `Scale` models + their translation models (same `BaseModel`/`TranslationBase` pattern, `unique_together` on `(model, language)`)
- [x] 1.4 Set Spanish `verbose_name`s on models: Disciplina, Técnica, Temática, Tipo de pieza (Format), Tamaño (Scale)
- [x] 1.5 Replace `Artwork.category`, `medium`, `surface` with M2M fields `disciplines`, `techniques`, `themes`, `formats`, `scales` (`related_name="artworks"`, `blank=True`)
- [x] 1.6 Generate migration `0002_*.py` via `makemigrations` (`DeleteModel`/`CreateModel` for taxonomies, `RemoveField` old FKs, `AddField` new M2M) — no data-copy step needed since the DB is empty

## 2. Fixtures

- [x] 2.1 Create `artworks/fixtures/artworks/Discipline.json` (6 rows) + `DisciplineTranslation.json` (12 es/en rows), explicit pk/slug/is_active/sort_order/timestamps
- [x] 2.2 Create `artworks/fixtures/artworks/Technique.json` (7 rows) + `TechniqueTranslation.json` (14 rows)
- [x] 2.3 Create `artworks/fixtures/artworks/Theme.json` (15 rows) + `ThemeTranslation.json` (30 rows)
- [x] 2.4 Create `artworks/fixtures/artworks/Format.json` (6 rows) + `FormatTranslation.json` (12 rows)
- [x] 2.5 Create `artworks/fixtures/artworks/Scale.json` (2 rows) + `ScaleTranslation.json` (4 rows)
- [x] 2.6 Keep pk/slugs exactly as the manifest in `specs/artwork-taxonomies/spec.md` (so seeds and tests reference the same PKs)

## 3. Seed fixtures (random sample data)

- [x] 3.1 Create `artworks/fixtures/artworks/seed/Artist.json` (3–5 sample artists, es/en bios)
- [x] 3.2 Create `artworks/fixtures/artworks/seed/ArtistTranslation.json`
- [x] 3.3 Create `artworks/fixtures/artworks/seed/Artwork.json` (random artworks referencing the base taxonomy PKs with varied M2M combinations/statuses)
- [x] 3.4 Create `artworks/fixtures/artworks/seed/ArtworkTranslation.json`

## 4. Fixture loader

- [x] 4.1 Create `core/management/commands/__init__.py`
- [x] 4.2 Create `core/management/commands/base_loaddata.py` (auto-discover every `<app>/fixtures/<app>/`, fail-soft, sorted order, per `specs/fixture-loading/spec.md`)
- [x] 4.3 Create `core/management/commands/seed_loaddata.py` (same for `<app>/fixtures/<app>/seed/`)
- [x] 4.4 Add `FIXTURE_DIRS` to `project/settings.py` (optional, per `docs/django-fixtures.md`)
- [x] 4.5 Wire `base_loaddata` after `migrate` into `Dockerfile` build and `start.sh`

## 5. Admin

- [x] 5.1 Register `DisciplineAdmin`, `TechniqueAdmin`, `ThemeAdmin`, `FormatAdmin`, `ScaleAdmin` (ModelAdminUnfoldBase + bilingual inline, slug/sort_order init) and remove any `Surface` registration
- [x] 5.2 Replace `CategoryTranslationInline`/`MediumTranslationInline` with the correct taxonomy inlines; add Theme/Format/Scale inlines
- [x] 5.3 Update `ArtworkAdmin` fieldsets: "Taxonomías" group with `disciplines`, `techniques`, `themes`, `formats`, `scales` via `filter_horizontal`
- [x] 5.4 Update `list_filter` to `["status", "is_active", "disciplines", "techniques", "themes", "formats", "scales"]`
- [x] 5.5 Update `search_fields`/`list_display` taxonomy fields and Spanish labels (no references to `category`/`medium`/`surface`)

## 6. Tests

- [x] 6.1 Update `artworks/tests.py` imports/creation for the new taxonomy models and delete Surface references
- [x] 6.2 Update Artwork test construction to M2M-based creation (no category/medium/surface args)
- [x] 6.3 Add admin tests for the new taxonomy admins and the M2M widgets on `ArtworkAdmin`
- [x] 6.4 Make fixture loading testable: `call_command("base_loaddata")` in relevant `setUp`; seed-loading covered once
- [x] 6.5 Ensure `makemigrations --check` and `manage.py test` pass

## 7. Verification

- [x] 7.1 Run `python manage.py makemigrations --check` + `migrate` (fresh DB)
- [x] 7.2 Run `python manage.py base_loaddata` and confirm the 36 taxonomy rows
- [x] 7.3 Run `python manage.py seed_loaddata` and confirm sample artists/artworks
- [x] 7.4 Open admin: taxonomy pages render, the artwork form shows 5 `filter_horizontal` widgets, changelist loads, no Surface leftovers
- [x] 7.5 Create an artwork with multiple themes/formats to confirm M2M saves across axes