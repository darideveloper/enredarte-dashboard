# Artist Location Specification

## Purpose
To define the `Location` model (a single text value with bilingual translations) and its foreign key on `Artist`, so one location can be shared by many artists, plus fixtures and admin management.

## ADDED Requirements

### Requirement: Location model
The system SHALL provide a `Location` model in `artworks/models.py` extending `BaseModel` (slug, `is_active`, `sort_order`, timestamps) with a bilingual `LocationTranslation` (`TranslationBase`, `unique_together` on `(location, language)`) holding the location's `name`.

#### Scenario: Creating a translatable location
- **WHEN** an administrator creates a Location
- **THEN** it can hold Spanish and English names, unique per language.

### Requirement: Single location per artist via FK
The system SHALL add a nullable `Artist.location` foreign key (`on_delete=SET_NULL`, `related_name="artists"`), allowing many artists to reference the same location.

#### Scenario: Assigning a location to an artist
- **WHEN** an administrator sets an artist's location to an existing Location (e.g. "Ciudad de México")
- **THEN** the artist references that single location, and the location's reverse relation includes the artist.

#### Scenario: Unassigned location
- **WHEN** an artist has no location set
- **THEN** the artist renders without a location and no error occurs.

### Requirement: Location admin
The system SHALL register `Location` in the Django admin with the standard bilingual translation inline (es/en prefilled when creating) and Spanish labels "Ubicación" / "Ubicaciones".

#### Scenario: Managing locations
- **WHEN** an administrator opens the Location admin
- **THEN** they can create/edit locations and their Spanish and English names.

### Requirement: Location fixtures
The system SHALL ship base fixtures `Location.json` + `LocationTranslation.json` with 4 stable-PK locations and es/en names, loaded by `base_loaddata`; the seed `Artist.json` rows SHALL reference those location PKs. The locations and their fixed PKs/un-accented kebab slugs SHALL be:

- 1 guadalajara · 2 jalisco · 3 occidente · 4 mexico

#### Scenario: Fresh environment locations
- **WHEN** `base_loaddata` runs on a fresh database
- **THEN** the 4 locations exist with Spanish and English names.

#### Scenario: Seeded artists have locations
- **WHEN** `seed_loaddata` runs after `base_loaddata`
- **THEN** the seeded artists reference the base location PKs without integrity errors.
