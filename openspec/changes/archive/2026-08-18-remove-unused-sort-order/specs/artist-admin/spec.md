# Artist Admin — Delta

Delta spec for the `artist-admin` capability.

## MODIFIED Requirements

### Requirement: Artist model admin registration
The system SHALL register the `Artist` model in `artworks/admin.py` using `ModelAdminUnfoldBase` so that artists are manageable within the Django Unfold admin site.

#### Scenario: Viewing artist list in admin
- **WHEN** an administrator opens the Django Admin panel
- **THEN** the sidebar SHALL display "Artistas" with a palette icon and list artists with columns for Name, Email, Birth Year, Death Year, and Active state in Spanish.

### Requirement: Social links inline on Artist admin
The system SHALL include the `ArtistSocialLinkInline` (`TabularInline`) in the `ArtistAdmin` edit form.

#### Scenario: Editing social links with the artist
- **WHEN** an administrator opens an Artist edit form
- **THEN** they can add and remove the artist's social links in place.