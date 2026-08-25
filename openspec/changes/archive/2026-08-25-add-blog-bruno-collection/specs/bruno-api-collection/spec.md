## MODIFIED Requirements

### Requirement: Collection committed to git
The system SHALL store a Bruno workspace in the `bruno/` directory at the repository root, so every request is a plain-text `.bru` file tracked in version control. `bruno/workspace.yml` SHALL declare the workspace with a `collections` list pointing at the collection folder. The collection SHALL contain model-specific folders for artworks (`Artists/`, `ArtCurators/`, `Locations/`, `Galleries/`, `Disciplines/`, `Techniques/`, `Themes/`, `Formats/`, `Scales/`, `Artworks/`) and a `Posts/` folder for blog posts, each with `GET list.bru` and `GET detail.bru` files. Nothing in `bruno/` SHALL require a runtime dependency or an entry in `requirements.txt`.

#### Scenario: Collection exists with per-model folders
- **WHEN** the repository is cloned
- **THEN** the `bruno/` directory exists with `workspace.yml`, `README.md`, and `collections/enredarte-dashboard-api/` containing 11 subdirectories (10 artwork models + `Posts/`), each with `.bru` request files.

#### Scenario: No runtime dependency introduced
- **WHEN** the change is applied
- **THEN** `requirements.txt` and Python runtime code are unchanged.
