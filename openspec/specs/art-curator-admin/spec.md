# art-curator-admin

## Requirements

### Requirement: ArtCurator model admin registration
The system SHALL register the `ArtCurator` model in `artworks/admin.py` using `ModelAdminUnfoldBase` with a layout grouped by fieldsets.

#### Scenario: Viewing the curator list in admin
- **WHEN** an administrator opens the Django Admin panel
- **THEN** the sidebar SHALL list curators with columns for Name, Email, and Active state.

### Requirement: Inline translation management for ArtCurator
The system SHALL display `ArtCuratorTranslation` as a `StackedInline` inside the `ArtCurator` edit form, pre-populating Spanish (`es`) and English (`en`) forms during creation and suppressing extras when translations exist.

#### Scenario: Creating a new curator
- **WHEN** an administrator creates a new ArtCurator
- **THEN** the translation inline forms SHALL render with default language selections set to Spanish and English.

### Requirement: ArtCurator has-galleries filter
The system SHALL add a "with/without galleries" filter to the `ArtCuratorAdmin` changelist so an administrator can identify curators who curate no galleries.

#### Scenario: Finding curators without galleries
- **WHEN** an administrator opens the ArtCurator changelist and selects the "sin galerías" lookup
- **THEN** only curators with no curated galleries SHALL be shown.

#### Scenario: Finding curators with galleries
- **WHEN** an administrator opens the ArtCurator changelist and selects the "con galerías" lookup
- **THEN** only curators curating at least one gallery SHALL be shown.
