## ADDED Requirements

### Requirement: ArtworkImage stores artwork photos

The system SHALL have an `ArtworkImage` model extending `BaseModel` with: `artwork` (ForeignKey to Artwork, CASCADE, related_name="images"), `image` (ImageField), `alt_es` (CharField, max_length=200, blank=True), `alt_en` (CharField, max_length=200, blank=True), `is_primary` (BooleanField, default=False), `sort_order` (IntegerField, default=0). Default ordering SHALL be `["sort_order"]`.

#### Scenario: Artwork with multiple images

- **WHEN** an Artwork has 3 ArtworkImage records
- **THEN** querying the artwork's images returns all 3

#### Scenario: Primary image flag

- **WHEN** an ArtworkImage has `is_primary=True`
- **THEN** it can be identified as the main image for the artwork

#### Scenario: Images ordered by sort_order

- **WHEN** creating images with sort_order 2, 0, 1
- **THEN** they are returned in order 0, 1, 2

#### Scenario: Cascade delete on artwork removal

- **WHEN** an Artwork is deleted
- **THEN** all associated ArtworkImage records are deleted
