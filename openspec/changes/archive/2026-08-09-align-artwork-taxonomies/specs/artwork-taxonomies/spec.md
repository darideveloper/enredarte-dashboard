## ADDED Requirements

### Requirement: Artwork taxonomy models

The system SHALL provide five translatable taxonomy models — `Discipline`, `Technique`, `Theme`, `Format`, and `Scale` — each extending `BaseModel` (slug, `is_active`, `sort_order`, timestamps) with a bilingual `<Model>Translation` (`TranslationBase`, `unique_together` on `(model, language)`), supporting the client's filter dimensions Disciplina, Técnica, Temática, Tipo de pieza (Format), and Tamaño (Scale).

#### Scenario: Taxonomy rows are translatable

- **WHEN** an administrator creates a taxonomy row (e.g. a Discipline)
- **THEN** it can hold Spanish and English names, and its name is unique per language.

### Requirement: All taxonomy links are ManyToMany on Artwork

The system SHALL replace `Artwork.category`, `medium`, and `surface` (single foreign keys) with ManyToMany fields: `disciplines`, `techniques`, `themes`, `formats`, and `scales` (`related_name="artworks"`, `blank=True`). `Artwork.artist` SHALL remain a single foreign key.

#### Scenario: An artwork can have several values per axis

- **WHEN** an administrator saves an Artwork selecting Disciplina "Pintura" and multiple Temas, e.g. "Feminismo" and "Memoria"
- **THEN** the artwork is related to "Pintura", "Feminismo", and "Memoria", and appears in each dimension's filter results.

#### Scenario: Artist remains single-valued

- **WHEN** an administrator assigns an artist to an artwork
- **THEN** the artwork has exactly one `artist` foreign key, unchanged from before.

### Requirement: Surface is removed

The system SHALL remove the `Surface` model, `SurfaceTranslation`, and the `surface` foreign key on `Artwork`.

#### Scenario: Surface no longer exists

- **WHEN** the migrations for this change are applied
- **THEN** no `Surface` or `SurfaceTranslation` model or `Artwork.surface` field exists in the schema or admin.

### Requirement: Client taxonomy seeded via base fixtures

The system SHALL seed the complete client taxonomy as base fixtures (loaded by `base_loaddata`) with explicit PKs, es/en names, and these exact values:

- Disciplinas: Pintura, Collage, Ilustración, Fotografía, Escultura, Street Art
- Técnicas: Acrílico, Óleo, Acuarela, Mixta, Tinta, Lápiz, Carboncillo
- Temas: Naturaleza, Retrato, Paisaje, Abstracto, Surrealismo, Urbano, Música, Cultura popular, Identidad, Memoria, Nostalgia, Feminismo, Ciencia ficción, Fantasía, Minimalismo
- Formatos (tipo de pieza): Obra original, Edición limitada, Prints, Series, Esculturas, Objetos
- Escalas (tamaño): Mini obras, Gran formato

#### Scenario: Fresh environment loads all taxonomy values

- **WHEN** `base_loaddata` runs on a fresh database
- **THEN** all 6 disciplinas, 7 técnicas, 15 temas, 6 formatos, and 2 escalas exist, each with a Spanish and an English name.

### Requirement: Stable fixture identities

The system SHALL fix the taxonomy PKs and un-accented kebab slugs in the base fixtures to the manifest below, so seed fixtures and tests can reference them by PK:

- Disciplinas: 1 pintura · 2 collage · 3 ilustracion · 4 fotografia · 5 escultura · 6 street-art
- Técnicas: 1 acrilico · 2 oleo · 3 acuarela · 4 mixta · 5 tinta · 6 lapiz · 7 carboncillo
- Temas: 1 naturaleza · 2 retrato · 3 paisaje · 4 abstracto · 5 surrealismo · 6 urbano · 7 musica · 8 cultura-popular · 9 identidad · 10 memoria · 11 nostalgia · 12 feminismo · 13 ciencia-ficcion · 14 fantasia · 15 minimalismo
- Formatos: 1 obra-original · 2 edicion-limitada · 3 prints · 4 series · 5 esculturas · 6 objetos
- Escalas: 1 mini-obras · 2 gran-formato

#### Scenario: Seeds reference stable PKs

- **WHEN** `seed_loaddata` imports artworks and artists
- **THEN** their taxonomy ManyToMany and FK references match the PKs above and load without integrity errors.

### Requirement: Taxonomy values admin

The system SHALL expose `Discipline`, `Technique`, `Theme`, `Format`, and `Scale` in the Django admin with the standard bilingual translation inline (es/en prefilled when creating) and Spanish labels (Disciplina · Técnica · Temática · Tipo de pieza · Tamaño).

#### Scenario: Creating a discipline via admin
- **WHEN** an administrator opens the Discipline admin add form
- **THEN** they can define an es/en via inline translation rows.

### Requirement: No Surface admin

The system SHALL unregister and remove the `Surface` admin registration so it no longer appears in the admin sidebar or artwork forms.

#### Scenario: Surface not visible in admin

- **WHEN** an administrator opens the admin sidebar
- **THEN** Surface is not listed, and artwork edit forms no longer show a surface selector.

### Requirement: Seed demo data (seed fixtures)

The system SHALL ship seed fixtures (`artworks/fixtures/artworks/seed/`) with random `Artist` and `Artwork` rows that reference the base taxonomy values, loaded once per environment via `seed_loaddata` and excluded from the base build.

#### Scenario: Loading demo content

- **WHEN** `seed_loaddata` runs on an environment that has run `base_loaddata`
- **THEN** sample artists and artworks exist whose discipline/technique/theme/format/scale references resolve to the seeded taxonomy rows.

#### Scenario: Bases load excludes demo content

- **WHEN** `base_loaddata` runs (build/bootstrap/tests)
- **THEN** no sample artists or demo artworks are created.