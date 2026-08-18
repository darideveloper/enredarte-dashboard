## MODIFIED Requirements

### Requirement: Image URLs use get_media_url
All image fields (`Artist.photo`, `ArtCurator.photo`, `Gallery.logo`, `ArtworkImage.image`) SHALL be serialized as absolute URLs using `get_media_url()` from `utils/media.py`. The project SHALL define `HOST` in `project/settings.py` (from the `HOST` environment variable) so the local-prefix branch of `get_media_url()` works. The env-specific dotenv file (`.env.{ENV}`) SHALL be loaded with `override=True` so project-defined values take precedence over shell-injected vars.

#### Scenario: HOST setting defined
- **WHEN** `project/settings.py` is loaded
- **THEN** it SHALL expose a `HOST` attribute read from the `HOST` environment variable.

#### Scenario: Env-specific dotenv overrides shell vars
- **WHEN** a shell-injected env var (e.g., from `portless`) conflicts with `.env.{ENV}`
- **THEN** the value from `.env.{ENV}` SHALL take precedence.

#### Scenario: Local media prefixed with HOST
- **WHEN** an artwork image is stored locally (not S3/DigitalOcean)
- **THEN** the image URL SHALL be prefixed with `settings.HOST`.

#### Scenario: S3 URLs passed through unchanged
- **WHEN** an image is stored on S3 or DigitalOcean Spaces
- **THEN** the image URL SHALL be returned as-is (the full object URL).

#### Scenario: Missing HOST falls back to relative URL
- **WHEN** `settings.HOST` is `None` or empty
- **THEN** `get_media_url` SHALL return the relative URL (e.g., `/media/artworks/obra-1.jpg`) without crashing.
