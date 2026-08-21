## Requirements

### Requirement: Content models display Spanish translated names

Every concrete model whose display name lives in translation rows (`Location`, `Gallery`, `Discipline`, `Technique`, `Theme`, `Format`, `Scale`) MUST return a content-based Spanish string from `__str__`, preferring the `es` translation, falling back to any available translation, and finally to the slug.

#### Scenario: Spanish translation present
- **WHEN** a content model has an `es` translation with a `name`
- **THEN** `str(model)` returns that Spanish name (e.g. `"Pintura"`)

#### Scenario: Spanish translation absent
- **WHEN** a content model has no `es` translation but has another language
- **THEN** `str(model)` returns the name of the available translation

#### Scenario: No translations
- **WHEN** a content model has no translations at all
- **THEN** `str(model)` returns the model's slug

### Requirement: Artwork displays Spanish translated title

`Artwork.__str__` MUST return its Spanish `title` from translations, falling back to any available translation, and finally to the slug.

#### Scenario: Spanish title present
- **WHEN** an artwork has an `es` translation with a `title`
- **THEN** `str(artwork)` returns the Spanish title

#### Scenario: Only English title present
- **WHEN** an artwork has only a non-Spanish translation
- **THEN** `str(artwork)` returns the title from the available translation

#### Scenario: No title translations
- **WHEN** an artwork has no title translations
- **THEN** `str(artwork)` returns the artwork's slug

### Requirement: Translation rows are self-describing

Every `*Translation` model (`ArtistTranslation`, `LocationTranslation`, `ArtCuratorTranslation`, `GalleryTranslation`, `DisciplineTranslation`, `TechniqueTranslation`, `ThemeTranslation`, `FormatTranslation`, `ScaleTranslation`, `ArtworkTranslation`) MUST return `"{parent} ({language})"` from `__str__`.

#### Scenario: Translation row rendering
- **WHEN** a translation row has a parent and a `language`
- **THEN** `str(row)` returns the parent's string followed by the language in parentheses (e.g. `"Guadalajara (es)"`)

### Requirement: Artist and ArtCurator display their name

`Artist.__str__` and `ArtCurator.__str__` MUST return the person's `name`.

#### Scenario: Artist rendering
- **WHEN** an artist has a `name`
- **THEN** `str(artist)` returns that name

#### Scenario: ArtCurator rendering
- **WHEN** an art curator has a `name`
- **THEN** `str(artcurator)` returns that name

### Requirement: Join models display content-based Spanish strings

`ArtistSocialLink`, `ArtworkGallery`, and `ArtworkImage` MUST return content-based strings from `__str__`.

#### Scenario: ArtistSocialLink rendering
- **WHEN** an artist social link has a `platform` and an artist
- **THEN** `str(link)` returns the Spanish platform label followed by an em dash and the artist's name (e.g. `"Instagram — Frida Kahlo"`)

#### Scenario: ArtworkGallery rendering
- **WHEN** an artwork-gallery link has an artwork and a gallery
- **THEN** `str(link)` returns the artwork string, `" en "`, and the gallery string (e.g. `"Memoria silente en Galería de Arte"`)

#### Scenario: ArtworkImage rendering with alt text
- **WHEN** an artwork image has a non-empty `alt_es`
- **THEN** `str(image)` returns the `alt_es` value

#### Scenario: ArtworkImage rendering without alt text
- **WHEN** an artwork image has an empty `alt_es`
- **THEN** `str(image)` returns `"Imagen de {artwork}"` using the artwork's string
