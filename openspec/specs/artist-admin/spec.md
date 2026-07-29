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
