## Requirements

### Requirement: Artist model admin registration
The system SHALL register the `Artist` model in `artworks/admin.py` using `ModelAdminUnfoldBase` so that artists are manageable within the Django Unfold admin site.

#### Scenario: Viewing artist list in admin
- **WHEN** an administrator opens the Django Admin panel
- **THEN** the sidebar SHALL display "Artistas" with a palette icon and list artists with columns for Name, Email, Birth Year, Death Year, Active state, and Sort Order in Spanish.

### Requirement: Inline translation management for Artist
The system SHALL display `ArtistTranslation` as a `StackedInline` inside the `Artist` edit form in Django Admin to allow editing Spanish (`es`) and English (`en`) bio text on the same page, pre-populating Spanish (`es`) on the first form and English (`en`) on the second form during creation, and suppressing extra blank forms when all translations already exist.

#### Scenario: Editing artist translations
- **WHEN** an administrator accesses an Artist change page in the admin
- **THEN** an inline section titled "Traducciones" SHALL render existing translations without appending extra blank forms when Spanish and English translations are present.

#### Scenario: Creating a new artist with pre-populated translation languages
- **WHEN** an administrator accesses the new Artist creation page in the admin
- **THEN** the two translation inline forms SHALL render with default language selections set to Spanish (`es`) and English (`en`).

### Requirement: Artist admin form field ordering
The system SHALL organize the `ArtistAdmin` form using `fieldsets` to logically group fields and ensure `slug` directly follows `name`.

#### Scenario: Creating or editing an artist
- **WHEN** an administrator views the Artist add or edit form
- **THEN** fields SHALL be organized into logical sections (e.g., Personal Info, Contact & Media, System Status) with the `slug` field positioned immediately after `name` to visually support auto-population.

### Requirement: Location selector on Artist admin
The system SHALL add the `location` field to the `ArtistAdmin` edit form so an administrator can assign a shared `Location` to an artist.

#### Scenario: Assigning an artist location
- **WHEN** an administrator opens an Artist edit form
- **THEN** they can pick one `Location` for the artist (or leave it empty).

### Requirement: Social links inline on Artist admin
The system SHALL include the `ArtistSocialLinkInline` (`TabularInline`, sortable via `sort_order`) in the `ArtistAdmin` edit form.

#### Scenario: Editing social links with the artist
- **WHEN** an administrator opens an Artist edit form
- **THEN** they can add, remove, and reorder the artist's social links in place.

### Requirement: Changelist summary columns on Artist admin
The system SHALL add readonly count columns to the `ArtistAdmin` changelist for the derived blocks (artworks, available works, techniques, highlighted works, galleries), computed from the `Artist` derived properties (see `artist-derived-fields`).

#### Scenario: Viewing artist counts
- **WHEN** an administrator opens the Artist changelist
- **THEN** each row shows the computed counts for the derived blocks.

### Requirement: Readonly Resumen fieldset on Artist admin
The system SHALL render the derived profile blocks on the `ArtistAdmin` change form as a readonly "Resumen" fieldset in full detail, computed from the `Artist` derived properties (see `artist-derived-fields`).

#### Scenario: Viewing computed profile blocks
- **WHEN** an administrator opens an Artist edit form
- **THEN** the "Resumen" section displays the computed techniques, available works count, new additions, highlighted works, most viewed, and exhibiting galleries.
