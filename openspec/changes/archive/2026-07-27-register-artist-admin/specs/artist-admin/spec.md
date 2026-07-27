## ADDED Requirements

### Requirement: Artist model admin registration
The system SHALL register the `Artist` model in `artworks/admin.py` using `ModelAdminUnfoldBase` so that artists are manageable within the Django Unfold admin site.

#### Scenario: Viewing artist list in admin
- **WHEN** an administrator opens the Django Admin panel
- **THEN** the sidebar SHALL display "Artistas" with a palette icon and list artists with columns for Name, Email, Birth Year, Death Year, Active state, and Sort Order in Spanish.

### Requirement: Inline translation management for Artist
The system SHALL display `ArtistTranslation` as a `StackedInline` inside the `Artist` edit form in Django Admin to allow editing Spanish (`es`) and English (`en`) bio text on the same page.

#### Scenario: Editing artist translations
- **WHEN** an administrator accesses an Artist change page in the admin
- **THEN** an inline section titled "Traducciones" SHALL render with fields for language selection and biography text areas for Spanish and English.
