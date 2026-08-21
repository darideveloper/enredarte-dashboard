# Bruno API Collection

## ADDED Requirements

### Requirement: Collection committed to git

The system SHALL store a Bruno workspace in the `bruno/` directory at the repository root, so every request is a plain-text `.bru` file tracked in version control. `bruno/workspace.yml` SHALL declare the workspace with a `collections` list pointing at the collection folder. Nothing in `bruno/` SHALL require a runtime dependency or an entry in `requirements.txt`.

#### Scenario: Collection exists in repo
- **WHEN** the repository is cloned
- **THEN** the `bruno/` directory exists and contains a `workspace.yml` file declaring the workspace, and a `collections/enredarte-dashboard-api/` folder whose `bruno.json` declares the collection metadata (name, type, version)

#### Scenario: No runtime dependency introduced
- **WHEN** the change is applied
- **THEN** `requirements.txt` and Python runtime code are unchanged

### Requirement: Environment variables for base URL and auth token

The system SHALL define a local environment file at `bruno/collections/enredarte-dashboard-api/environments/dev.bru` exposing two variables: `base_url` (the local dev server, reachable via the portless subdomain `https://enredarte-dashboard.localhost` started by `dev.sh`) and `token` (a DRF Token placeholder to be filled by the developer). Request files SHALL reference only these variables (e.g. `{{base_url}}`, `{{token}}`) and SHALL NOT hard-code hostnames or tokens.

#### Scenario: Local environment defines base_url and token
- **WHEN** the `dev.bru` environment is opened in Bruno
- **THEN** it exposes `base_url` (defaulting to `https://enredarte-dashboard.localhost`) and `token` variables with descriptive comments

#### Scenario: Request uses variables, not literals
- **WHEN** any request file is inspected
- **THEN** its URL and headers reference `{{base_url}}` and `{{token}}` and contain no hard-coded host or credential

### Requirement: Public catalog request

The system SHALL provide a request file for `GET /api/catalog/` that requires no authentication (`auth: none`) and targets `{{base_url}}/api/catalog/`.

#### Scenario: Catalog request hits the public endpoint
- **WHEN** the catalog request runs against the local server with the `dev` environment
- **THEN** the request sends `GET {{base_url}}/api/catalog/` without an `Authorization` header and the server returns `200` with the catalog payload (`generated_at`, `artists`, `taxonomies`, `locations`, `artworks`)

### Requirement: Authenticated router-root request

The system SHALL provide a request file for `GET /api/` (DRF router root) that sends the header `Authorization: Token {{token}}`.

#### Scenario: Router-root request with token
- **WHEN** the router-root request runs with the `dev` environment and a valid token value
- **THEN** the request sends `GET {{base_url}}/api/` with `Authorization: Token {{token}}` and the server returns `200` with the (currently empty) list of registered API routes

#### Scenario: Router-root request without valid token
- **WHEN** the router-root request runs with an empty or invalid token
- **THEN** the server returns `401` with the `{status, message, data}` error envelope

### Requirement: README documents usage

The system SHALL provide `bruno/README.md` explaining how to open the workspace in the Bruno desktop app (via **Workspace dropdown → Open workspace**, selecting the `bruno/` folder) and how to obtain a DRF Token (Django shell command per `docs/django-drf.md` §6) to place in `dev.bru`.

#### Scenario: README explains opening and token creation
- **WHEN** a developer reads `bruno/README.md`
- **THEN** it contains steps to open the `bruno/` workspace in Bruno, and a shell snippet to create a DRF Token and paste it into `dev.bru`
