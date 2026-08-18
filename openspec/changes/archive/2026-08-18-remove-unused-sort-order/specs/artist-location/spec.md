# Artist Location — Delta

Delta spec for the `artist-location` capability.

## MODIFIED Requirements

### Requirement: Location model
The system SHALL provide a `Location` model in `artworks/models.py` extending `BaseModel` (slug, `is_active`, timestamps) with a bilingual `LocationTranslation` (`TranslationBase`, `unique_together` on `(location, language)`) holding the location's `name`. The `Location` model SHALL NOT have a `sort_order` field.

#### Scenario: Creating a translatable location
- **WHEN** an administrator creates a Location
- **THEN** it can hold Spanish and English names, unique per language.

#### Scenario: Location has no sort_order
- **WHEN** the Location model is inspected
- **THEN** it SHALL NOT expose a `sort_order` field in its schema, admin form, or serialized output.