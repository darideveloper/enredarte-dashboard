# Admin Spanish Labels — Delta

Delta spec for the `admin-spanish-labels` capability.

## MODIFIED Requirements

### Requirement: Model field labels render in Spanish
Every concrete model field shown in the admin SHALL display a Spanish label, including fields inherited from the abstract base models (`created_at`, `updated_at`, `slug`, `is_active`, `language`, `name`, `email`, `website`, `photo`) and concrete fields (`birth_year`, `death_year`, `location`, `bio`, `platform`, `url`, `logo`, `curator`, `description`, `year`, `dimensions`, `price_mxn`, `price_usd`, `status`, `is_highlighted`, `views_count`, `title`, `image`, `alt_es`, `alt_en`, `is_primary`, `sort_order`). The `sort_order` field SHALL exist only on `ArtworkGallery` and `ArtworkImage` and SHALL display the label "Orden".

#### Scenario: Artist change form shows Spanish field labels
- **WHEN** a user opens the Artist change form in the admin
- **THEN** the fields display Spanish labels (e.g. "Creado el", "Nombre", "Correo electrónico", "Año de nacimiento", "Año de fallecimiento", "Ubicación") instead of the auto-generated English names ("created at", "name", "birth year", …)

#### Scenario: Translation inline shows Spanish language label
- **WHEN** a translation inline (e.g. ArtistTranslation) renders
- **THEN** the `language` field shows "Idioma" and the FK shows the Spanish model name

#### Scenario: Remaining sort_order fields labeled in Spanish
- **WHEN** the `ArtworkGallery` or `ArtworkImage` admin form renders
- **THEN** the `sort_order` field SHALL display the label "Orden".