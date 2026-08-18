## ADDED Requirements

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

### Requirement: Model names render in Spanish
The models `Artist`, `ArtCurator`, `Gallery`, and `Artwork` SHALL display Spanish singular/plural names in the admin sidebar, index, breadcrumbs, and titles.

#### Scenario: Artwork appears with Spanish name in sidebar
- **WHEN** the admin index/sidebar lists the artworks app
- **THEN** the model appears as "Obra de arte" (singular) and "Obras de arte" (plural) instead of "artwork"/"artworks"

#### Scenario: Gallery appears with Spanish name in sidebar
- **WHEN** the admin index/sidebar lists the artworks app
- **THEN** the model appears as "Galería"/"Galerías" instead of "gallery"/"gallerys"

#### Scenario: Artist appears with Spanish name
- **WHEN** the admin index/sidebar lists the artworks app
- **THEN** the model appears as "Artista"/"Artistas" instead of "artist"/"artists"

#### Scenario: ArtCurator appears with Spanish name
- **WHEN** the admin index/sidebar lists the artworks app
- **THEN** the model appears as "Curador de arte"/"Curadores de arte" instead of "art curator"/"art curators"

### Requirement: Choice dropdowns and badges show Spanish labels
`ArtworkStatus` and `ArtistSocialLink.Platform` choice fields SHALL display Spanish labels in dropdowns, list filters, and badges while their stored DB values remain unchanged (English codes).

#### Scenario: Artwork status dropdown shows Spanish
- **WHEN** a user edits an Artwork's status or filters the changelist by status
- **THEN** the options render as "Disponible", "Vendida", "Reservada", "En préstamo", "No disponible"
- **AND** the stored values remain `available`, `sold`, `reserved`, `on_loan`, `not_available`

#### Scenario: Social link platform dropdown shows Spanish for Other
- **WHEN** a user edits an ArtistSocialLink platform
- **THEN** the "Other" option renders as "Otra" while brand names (Instagram, Facebook, …) stay unchanged and the stored value remains `other`

### Requirement: App names render in Spanish
The `core` and `artworks` app configs SHALL expose Spanish `verbose_name`s so the admin sidebar and index group headings read in Spanish.

#### Scenario: Sidebar shows Spanish app name for artworks
- **WHEN** the admin sidebar renders the app list
- **THEN** the `artworks` app shows "Obras" instead of "Artworks"

#### Scenario: Core app name is set for future use
- **WHEN** the `core` app config is loaded
- **THEN** its `verbose_name` reads "Principal" so that if `core` registers admin models in the future the sidebar shows "Principal" instead of "Core"

### Requirement: Admin definitions use Spanish copy
Fieldset titles and the row-actions "Edit" button in the admin SHALL render in Spanish.

#### Scenario: Fieldset titles are Spanish
- **WHEN** a user opens a change form (Artist, ArtCurator, Gallery, Artwork, taxonomy models)
- **THEN** all fieldset headers render in Spanish (e.g. "Datos personales", "Contacto y medios", "Estado del sistema", "Información del sistema", "Información básica", "Atributos principales", "Comercial y estado", "Configuración del sistema")

#### Scenario: Row-action button is Spanish
- **WHEN** the row actions render on a changelist
- **THEN** the edit action shows "Editar" instead of "Edit"
