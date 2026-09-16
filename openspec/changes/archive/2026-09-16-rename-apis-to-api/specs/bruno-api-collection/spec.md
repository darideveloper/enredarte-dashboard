## MODIFIED Requirements

### Requirement: Environment variables for base URL and auth token
The system SHALL preserve the local environment file at `bruno/collections/enredarte-dashboard-api/environments/dev.bru` exposing two variables: `base_url` (the local dev server) and `token` (a DRF Token placeholder to be filled by the developer). The `.bru` environment file SHALL be gitignored; the committed template is `dev.bru.example` with a placeholder `token`, copied to `dev.bru` locally. All request files SHALL reference `{{base_url}}/api/artworks/<resource>/` or `{{base_url}}/api/artworks/<resource>/1/` and `{{token}}`, and SHALL NOT hard-code hostnames or tokens.

#### Scenario: Local environment defines base_url and token
- **WHEN** the `dev.bru` environment is opened in Bruno
- **THEN** it exposes `base_url` and `token` variables with descriptive comments, and `dev.bru` is untracked while `dev.bru.example` holds the placeholder template

#### Scenario: Request uses variables, not literals
- **WHEN** any request file is inspected
- **THEN** its URL SHALL reference `{{base_url}}/api/artworks/<resource>/` or `{{base_url}}/api/artworks/<resource>/1/` and its headers SHALL reference `{{token}}`.

### Requirement: README documents usage
The system SHALL provide `bruno/README.md` documenting the new 10-model endpoint structure under `/api/artworks/` and how to use the per-model request files. It SHALL describe the `/api/artworks/` URL prefix and SHALL include instructions for obtaining a DRF Token (Django shell command per `docs/django-drf.md` §6) to place in `dev.bru`.

#### Scenario: README explains new structure
- **WHEN** a developer reads `bruno/README.md`
- **THEN** it SHALL describe the 10 model-specific request folders and how to use them, and SHALL include instructions for obtaining a DRF Token.
