## ADDED Requirements

### Requirement: Artist represents an art creator

The system SHALL have an `Artist` model extending `Person` with: `birth_year` (IntegerField, null, blank), `death_year` (IntegerField, null, blank). The `ArtistTranslation` model SHALL have: `artist` (ForeignKey to Artist, CASCADE), `language`, `bio` (TextField, blank). `unique_together = [("artist", "language")]`.

#### Scenario: Artist with complete data

- **WHEN** creating an Artist with name, birth_year, website
- **THEN** all fields are stored correctly

#### Scenario: Artist translation bio per language

- **WHEN** creating an ArtistTranslation with language "es" and a bio
- **THEN** querying translations returns the Spanish bio for that language

### Requirement: ArtCurator represents an art curator

The system SHALL have an `ArtCurator` model extending `Person` with no additional fields. The `ArtCuratorTranslation` model SHALL have: `art_curator` (ForeignKey, CASCADE), `language`, `bio` (TextField, blank). `unique_together = [("art_curator", "language")]`.

#### Scenario: Curator can be deleted without affecting galleries

- **WHEN** a curator is deleted
- **THEN** associated Gallery records set curator to null

### Requirement: Gallery represents a website section

The system SHALL have a `Gallery` model extending `BaseModel` with: `logo` (ImageField, null, blank), `curator` (ForeignKey to ArtCurator, SET_NULL, null, blank, related_name="curated_galleries"). The `GalleryTranslation` model SHALL have: `gallery` (ForeignKey, CASCADE), `language`, `name` (CharField, max_length=200), `description` (TextField, blank). `unique_together = [("gallery", "language")]`.

#### Scenario: Gallery with bilingual name

- **WHEN** creating GalleryTranslations for "es" and "en"
- **THEN** each language SHALL have its own name

#### Scenario: Gallery curator set to null on curator deletion

- **WHEN** a curator assigned to a Gallery is deleted
- **THEN** the Gallery's curator field is set to null

### Requirement: Artwork is the central domain entity

The system SHALL have an `Artwork` model extending `BaseModel` with: `artist` (ForeignKey to Artist, PROTECT, related_name="artworks"), `year` (IntegerField), `dimensions` (CharField, max_length=100), `medium` (ForeignKey to Medium, PROTECT), `surface` (ForeignKey to Surface, PROTECT), `category` (ForeignKey to Category, PROTECT), `price_mxn` (DecimalField, max_digits=10, decimal_places=2), `price_usd` (DecimalField, max_digits=10, decimal_places=2), `status` (CharField, max_length=20, choices).

#### Scenario: Full artwork creation

- **WHEN** creating an Artwork with all required FK fields and prices
- **THEN** the artwork is stored with a unique slug

#### Scenario: Artwork status choices enforced

- **WHEN** setting status to an invalid value
- **THEN** Django SHALL raise a ValidationError

#### Scenario: Artist deletion blocked when artworks exist

- **WHEN** attempting to delete an Artist that has associated Artworks
- **THEN** the delete SHALL be blocked

#### Scenario: Taxonomy fields are protected from deletion

- **WHEN** attempting to delete a Medium that has associated Artworks
- **THEN** the delete SHALL be blocked

### Requirement: ArtworkTranslation provides bilingual title and description

The `ArtworkTranslation` model SHALL have: `artwork` (ForeignKey, CASCADE, related_name="translations"), `language`, `title` (CharField, max_length=200), `description` (TextField, blank). `unique_together = [("artwork", "language")]`.

#### Scenario: Artwork queried by language

- **WHEN** an Artwork has both ES and EN translations
- **THEN** filtering translations by language returns the correct title

### Requirement: ArtworkGallery manages M2M between Artwork and Gallery

The `ArtworkGallery` through model (extends `BaseModel`) SHALL have: `artwork` (ForeignKey to Artwork, CASCADE), `gallery` (ForeignKey to Gallery, CASCADE), `sort_order` (IntegerField, default=0). `unique_together = [("artwork", "gallery")]`.

#### Scenario: Artwork appears in multiple galleries

- **WHEN** an Artwork is linked to 2 galleries via ArtworkGallery
- **THEN** querying the artwork's galleries returns both

#### Scenario: Duplicate artwork-gallery pair prevented

- **WHEN** creating a duplicate ArtworkGallery entry
- **THEN** the system SHALL raise an IntegrityError
