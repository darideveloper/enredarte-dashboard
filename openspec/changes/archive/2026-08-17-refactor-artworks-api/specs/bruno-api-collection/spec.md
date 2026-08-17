# Bruno API Collection Specification (Delta)

## Purpose

This delta spec captures the rewriting of the Bruno API collection to cover the 10 per-model endpoints defined in `artworks-api-bruno`, replacing the old collection that only covered `GET /api/catalog/` and `GET /api/`.

## REMOVED Requirements

### Requirement: Public catalog request
**Reason**: The `GET /api/catalog/` endpoint is removed (see `public-catalog-api` delta spec). Its corresponding `Authenticated Catalog/GET catalog.bru` request file is deleted.

**Migration**: Use the 10 per-model request files under `bruno/collections/enredarte-dashboard-api/<Model>/GET list.bru`. For equivalent data, combine results from the individual model endpoints.

### Requirement: Authenticated router-root request
**Reason**: The DRF router is now registered under `apis/artworks/` instead of at the root `api/` level. The old `Auth/GET api root.bru` file targeting `GET /api/` is deleted.

**Migration**: Use `GET {{base_url}}/apis/artworks/` to see the new router root with registered endpoints. A dedicated Bruno request for this is not provided (use the collection's folder structure as reference instead).

## MODIFIED Requirements

### Requirement: Collection committed to git
The system SHALL store a Bruno workspace in the `bruno/` directory at the repository root, so every request is a plain-text `.bru` file tracked in version control. `bruno/workspace.yml` SHALL declare the workspace with a `collections` list pointing at the collection folder. The collection SHALL contain 10 model-specific folders (`Artists/`, `ArtCurators/`, `Locations/`, `Galleries/`, `Disciplines/`, `Techniques/`, `Themes/`, `Formats/`, `Scales/`, `Artworks/`), each with `GET list.bru` and `GET detail.bru` files. Nothing in `bruno/` SHALL require a runtime dependency or an entry in `requirements.txt`.

#### Scenario: Collection exists with per-model folders
- **WHEN** the repository is cloned
- **THEN** the `bruno/` directory exists with `workspace.yml`, `README.md`, and `collections/enredarte-dashboard-api/` containing 10 subdirectories (one per model) each with two `.bru` files.

#### Scenario: No runtime dependency introduced
- **WHEN** the change is applied
- **THEN** `requirements.txt` and Python runtime code are unchanged.

### Requirement: Environment variables for base URL and auth token
The system SHALL preserve the existing `dev.bru` environment file with `base_url` and `token` variables. All 20 new request files SHALL reference `{{base_url}}` and `{{token}}` and SHALL NOT hard-code hostnames or tokens.

#### Scenario: Request uses variables, not literals
- **WHEN** any of the 20 request files is inspected
- **THEN** its URL SHALL reference `{{base_url}}/apis/artworks/<resource>/` or `{{base_url}}/apis/artworks/<resource>/1/` and its headers SHALL reference `{{token}}`.

### Requirement: README documents usage
The system SHALL update `bruno/README.md` to document the new 10-model endpoint structure. It SHALL explain how to use the per-model request files and describe the `/apis/artworks/` URL prefix.

#### Scenario: README explains new structure
- **WHEN** a developer reads `bruno/README.md`
- **THEN** it SHALL describe the 10 model-specific request folders and how to use them, and SHALL include instructions for obtaining a DRF Token.
