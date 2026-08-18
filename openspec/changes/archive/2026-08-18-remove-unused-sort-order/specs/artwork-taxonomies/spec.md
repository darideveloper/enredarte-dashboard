# Artwork Taxonomies — Delta

Delta spec for the `artwork-taxonomies` capability.

## MODIFIED Requirements

### Requirement: Artwork taxonomy models
The system SHALL provide five translatable taxonomy models — `Discipline`, `Technique`, `Theme`, `Format`, and `Scale` — each extending `BaseModel` (slug, `is_active`, timestamps) with a bilingual `<Model>Translation` (`TranslationBase`, `unique_together` on `(model, language)`), supporting the client's filter dimensions Disciplina, Técnica, Temática, Tipo de pieza (Format), and Tamaño (Scale). Taxonomy models SHALL NOT have a `sort_order` field.

#### Scenario: Taxonomy rows are translatable
- **WHEN** an administrator creates a taxonomy row (e.g. a Discipline)
- **THEN** it can hold Spanish and English names, and its name is unique per language.

#### Scenario: Taxonomy rows have no sort_order
- **WHEN** a taxonomy model is inspected
- **THEN** it SHALL NOT expose a `sort_order` field in its schema, admin forms, or serialized output.