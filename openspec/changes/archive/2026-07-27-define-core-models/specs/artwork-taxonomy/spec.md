## ADDED Requirements

### Requirement: Category classifies artworks

The system SHALL have a `Category` model extending `BaseModel` with no additional fields. The `CategoryTranslation` model SHALL have: `category` (ForeignKey, CASCADE, related_name="translations"), `language`, `name` (CharField, max_length=200), `description` (TextField, blank). `unique_together = [("category", "language")]`.

#### Scenario: Category with bilingual name

- **WHEN** creating CategoryTranslations for "es" and "en"
- **THEN** each language SHALL have its own name
- **THEN** the slug remains shared across translations

#### Scenario: Category protected from deletion when in use

- **WHEN** a Category has associated Artworks
- **THEN** deleting the Category SHALL be prevented

### Requirement: Medium represents artistic technique/material

The system SHALL have a `Medium` model extending `BaseModel` with no additional fields. The `MediumTranslation` model SHALL have: `medium` (ForeignKey, CASCADE, related_name="translations"), `language`, `name` (CharField, max_length=200). `unique_together = [("medium", "language")]`.

#### Scenario: Medium with bilingual name

- **WHEN** creating MediumTranslations for "es" and "en"
- **THEN** each language SHALL have its own name

### Requirement: Surface represents the painting support

The system SHALL have a `Surface` model extending `BaseModel` with no additional fields. The `SurfaceTranslation` model SHALL have: `surface` (ForeignKey, CASCADE, related_name="translations"), `language`, `name` (CharField, max_length=200). `unique_together = [("surface", "language")]`.

#### Scenario: Surface with bilingual name

- **WHEN** creating SurfaceTranslations for "es" and "en"
- **THEN** each language SHALL have its own name
