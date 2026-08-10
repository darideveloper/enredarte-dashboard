# Slug Auto-Generation Specification

## Purpose

To define automatic, DRY slug generation for every slug-bearing model so that slugs are filled in from natural content (translation names/titles, composite identifiers, or tokens) without manual entry, while never overwriting user-provided values.

## Requirements

### Requirement: Shared unique slug helper
The system SHALL provide a reusable `unique_slugify(base, queryset)` helper (in `core/models.py`) that slugifies a base string and, if the resulting slug already exists in the given queryset, appends a numeric suffix (`-1`, `-2`, …) until a unique value is found.

#### Scenario: No collision
- **WHEN** a base slug does not exist in the queryset
- **THEN** the helper returns the slugified base unchanged (e.g. `pintura`).

#### Scenario: Collision on first attempt
- **WHEN** the base slug already exists in the queryset
- **THEN** the helper returns the base with the next free numeric suffix (e.g. `pintura-1`, then `pintura-2` if needed).

#### Scenario: Slugified input
- **WHEN** the base contains spaces, accents, and uppercase letters
- **THEN** the helper returns a lowercase, URL-safe slug (e.g. `Arte Abstracto` → `arte-abstracto`).

### Requirement: Empty slug allowed by validation
The `BaseModel.slug` field SHALL be `blank=True` (keeping `unique=True`, `max_length=200`) so that model forms validate while the slug is still empty and generation runs afterward.

#### Scenario: Saving a model with an empty slug
- **WHEN** a model instance is saved without a slug
- **THEN** form and model validation does not reject the empty slug.

### Requirement: Never overwrite an existing slug
Auto-generation SHALL run only when the slug is empty and SHALL never modify a user-provided or previously generated slug.

#### Scenario: Existing slug preserved
- **WHEN** an instance already has a slug and is saved again
- **THEN** the slug is left unchanged.

### Requirement: Translation-derived slugs via shared backfill mixin
The system SHALL provide an abstract `SlugBackfillMixin` (in `core/models.py`) that, after saving a translation row, backfills the parent's slug from the translation's ES content when the parent's slug is empty. The mixin SHALL be applied to the translation models for `Location`, `Gallery`, `Discipline`, `Technique`, `Theme`, `Format`, and `Scale`, deriving the slug from the ES `name` field.

#### Scenario: Creating a translated object in the admin
- **WHEN** an administrator creates a `Discipline` and its ES translation (`name="Pintura"`) through the translation inline
- **THEN** the parent `Discipline.slug` is set to `pintura` after the translation is saved.

#### Scenario: Creating a translated object via ORM
- **WHEN** a parent object is created and then an ES translation is saved via the ORM
- **THEN** the parent slug is backfilled from the ES translation name.

#### Scenario: Colliding translated slugs
- **WHEN** two parents share the same ES name and both would receive the same slug
- **THEN** the second parent receives a unique suffixed slug (e.g. `oleo-1`).

#### Scenario: ES translation missing
- **WHEN** only a non-ES translation exists (or none at all) and the parent slug is empty
- **THEN** the parent slug is not backfilled and remains empty rather than raising an error.

### Requirement: Artwork composite slug
The `ArtworkTranslation` model SHALL use the `SlugBackfillMixin` with a composite slug base of `{artist.slug}-{title}` from the ES translation title (e.g. artist `frida-kahlo`, title "Las Dos Fridas" → `frida-kahlo-las-dos-fridas`).

#### Scenario: Creating an artwork translation
- **WHEN** an administrator adds the ES translation for an artwork whose artist has slug `frida-kahlo` and whose ES title is `Las Dos Fridas`
- **THEN** the artwork slug becomes `frida-kahlo-las-dos-fridas`.

#### Scenario: Composite slug uniqueness
- **WHEN** two artworks by different artists share the same ES title
- **THEN** each receives a distinct slug because the artist slug prefixes the title.

#### Scenario: Composite slug collision
- **WHEN** two artworks by the same artist share the same ES title
- **THEN** the second receives a unique suffixed slug (e.g. `frida-kahlo-las-dos-fridas-1`).

### Requirement: Token slugs for inline-only models
`ArtworkGallery` and `ArtworkImage` SHALL auto-generate a unique random-token slug via a `save()` override when the slug is empty, so rows created through their admin inlines (which do not expose the slug field) always save successfully.

#### Scenario: Creating the first inline row
- **WHEN** an administrator adds an `ArtworkImage` to an artwork through the inline
- **THEN** the row saves with a generated token slug.

#### Scenario: Creating multiple inline rows
- **WHEN** an administrator adds several `ArtworkImage` or `ArtworkGallery` rows to the same parent
- **THEN** every row saves with a distinct token slug and no UNIQUE constraint violation occurs.

### Requirement: Existing admin slug behaviors preserved
The existing automatic slug behaviors for `Artist` and `ArtCurator` (admin `prepopulated_fields` from `name`) SHALL continue to work unchanged.

#### Scenario: Artist and curator forms
- **WHEN** an administrator types a name on an Artist or ArtCurator form
- **THEN** the slug field is auto-populated from the name and saved.

### Requirement: Fixture compatibility
Auto-generation SHALL not interfere with fixture loading: fixture rows that carry explicit slugs SHALL keep them.

#### Scenario: Loading seed fixtures
- **WHEN** `seed_loaddata` loads fixture rows that include explicit slug values
- **THEN** those slugs are preserved and no backfill overwrites them.
