# Art Curator Admin — Delta

Delta spec for the `art-curator-admin` capability.

## MODIFIED Requirements

### Requirement: ArtCurator model admin registration
The system SHALL register the `ArtCurator` model in `artworks/admin.py` using `ModelAdminUnfoldBase` with a layout grouped by fieldsets.

#### Scenario: Viewing the curator list in admin
- **WHEN** an administrator opens the Django Admin panel
- **THEN** the sidebar SHALL list curators with columns for Name, Email, and Active state.

## REMOVED Requirements

### Requirement: Auto-fill sort_order on ArtCurator creation form
**Reason**: The `sort_order` field is being removed from `ArtCurator`; `sort_order` is retained only on `ArtworkGallery` and `ArtworkImage`. There is no longer any ordering concept to pre-populate.
**Migration**: Remove the `get_changeform_initial_data` override on `ArtCuratorAdmin`; no behavior replaces it.