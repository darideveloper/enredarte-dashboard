## ADDED Requirements

### Requirement: TimeStampedModel provides auto-timestamps

All models SHALL inherit from `TimeStampedModel` which provides `created_at` and `updated_at` auto-managed DateTime fields.

#### Scenario: Automatic timestamps on creation

- **WHEN** a new model instance is saved
- **THEN** `created_at` and `updated_at` are set to the current timestamp

#### Scenario: Updated at refreshes on modification

- **WHEN** an existing model instance is saved
- **THEN** `updated_at` is updated to the current timestamp
- **THEN** `created_at` remains unchanged

### Requirement: BaseModel extends TimeStampedModel with common fields

All domain models SHALL inherit from `BaseModel` (extends `TimeStampedModel`) which provides `slug` (SlugField, unique, max_length=200), `is_active` (BooleanField, default=True), and `sort_order` (IntegerField, default=0).

#### Scenario: Slug enforces uniqueness per model

- **WHEN** two instances share the same slug value
- **THEN** the second save raises an IntegrityError

#### Scenario: Inactive items excluded from queries

- **WHEN** querying active items
- **THEN** instances with `is_active=False` are excluded

### Requirement: TranslationBase enables bilingual text

`TranslationBase` SHALL be an abstract model with a `language` field (CharField, max_length=5, choices=settings.LANGUAGES). Subclasses SHALL define `unique_together = [("<fk_field>", "language")]`.

#### Scenario: One translation per language per parent

- **WHEN** creating a second translation for the same parent and language
- **THEN** the system SHALL raise an IntegrityError

### Requirement: Person abstract base model

`Person` SHALL be an abstract model extending `BaseModel` with fields: `name` (CharField, max_length=200), `email` (EmailField, null, blank), `website` (URLField, null, blank), `photo` (ImageField, null, blank).

#### Scenario: Artist inherits Person fields

- **WHEN** creating an Artist
- **THEN** it SHALL have name, email, website, and photo fields from Person

### Requirement: LANGUAGES setting

The project settings SHALL define `LANGUAGES = [('es', 'Español'), ('en', 'English')]`.

#### Scenario: All translation models iterate over LANGUAGES

- **WHEN** registering a new translation
- **THEN** `language` MUST be one of the defined `LANGUAGES` choices
