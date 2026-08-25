# Bruno API Collection Specification

## Purpose
To define a Bruno API collection committed to the repository so developers can exercise the REST API (10 per-model endpoints under `/apis/artworks/`) against the local dev server without hard-coding hostnames or credentials. The workspace lives in `bruno/` as plain-text `.bru` files, uses a `dev.bru` environment exposing `base_url` and `token` variables (gitignored; only the `dev.bru.example` template is committed), and ships a `bruno/README.md` explaining how to open the workspace and obtain a DRF Token.

## Requirements

### Requirement: Collection committed to git
The system SHALL store a Bruno workspace in the `bruno/` directory at the repository root, so every request is a plain-text `.bru` file tracked in version control. `bruno/workspace.yml` SHALL declare the workspace with a `collections` list pointing at the collection folder. The collection SHALL contain model-specific folders for artworks (`Artists/`, `ArtCurators/`, `Locations/`, `Galleries/`, `Disciplines/`, `Techniques/`, `Themes/`, `Formats/`, `Scales/`, `Artworks/`) and a `Posts/` folder for blog posts, each with `GET list.bru` and `GET detail.bru` files. Nothing in `bruno/` SHALL require a runtime dependency or an entry in `requirements.txt`.

#### Scenario: Collection exists with per-model folders
- **WHEN** the repository is cloned
- **THEN** the `bruno/` directory exists with `workspace.yml`, `README.md`, and `collections/enredarte-dashboard-api/` containing 11 subdirectories (10 artwork models + `Posts/`), each with `.bru` request files.

#### Scenario: No runtime dependency introduced
- **WHEN** the change is applied
- **THEN** `requirements.txt` and Python runtime code are unchanged.

### Requirement: Environment variables for base URL and auth token
The system SHALL preserve the local environment file at `bruno/collections/enredarte-dashboard-api/environments/dev.bru` exposing two variables: `base_url` (the local dev server) and `token` (a DRF Token placeholder to be filled by the developer). The `.bru` environment file SHALL be gitignored; the committed template is `dev.bru.example` with a placeholder `token`, copied to `dev.bru` locally. All request files SHALL reference `{{base_url}}/apis/artworks/<resource>/` or `{{base_url}}/apis/artworks/<resource>/1/` and `{{token}}`, and SHALL NOT hard-code hostnames or tokens.

#### Scenario: Local environment defines base_url and token
- **WHEN** the `dev.bru` environment is opened in Bruno
- **THEN** it exposes `base_url` and `token` variables with descriptive comments, and `dev.bru` is untracked while `dev.bru.example` holds the placeholder template

#### Scenario: Request uses variables, not literals
- **WHEN** any request file is inspected
- **THEN** its URL SHALL reference `{{base_url}}/apis/artworks/<resource>/` or `{{base_url}}/apis/artworks/<resource>/1/` and its headers SHALL reference `{{token}}`.

### Requirement: README documents usage
The system SHALL provide `bruno/README.md` documenting the new 10-model endpoint structure under `/apis/artworks/` and how to use the per-model request files. It SHALL describe the `/apis/artworks/` URL prefix and SHALL include instructions for obtaining a DRF Token (Django shell command per `docs/django-drf.md` §6) to place in `dev.bru`.

#### Scenario: README explains new structure
- **WHEN** a developer reads `bruno/README.md`
- **THEN** it SHALL describe the 10 model-specific request folders and how to use them, and SHALL include instructions for obtaining a DRF Token.
