## Why

API image URLs (e.g., `ArtworkImage.image`, `Artist.photo`, `Gallery.logo`) return `127.0.0.1/media/...` instead of the configured `HOST` env variable (`http://enredarte.localhost`). Root cause: `portless` (the dev proxy) injects `HOST=127.0.0.1` into the shell environment, and `load_dotenv()` does not override existing env vars by default — so `.env.dev`'s `HOST` value is silently ignored.

## What Changes

- `project/settings.py`: Use `load_dotenv(override=True)` for the env-specific `.env.{ENV}` file so it wins over shell-injected vars.
- `utils/media.py`: Make `get_media_url` robust against `settings.HOST` being `None` or missing a protocol prefix (defense-in-depth).
- `docs/django-project-setup.md`: Update dotenv loading snippet and `get_media_url` code example to reflect the new behavior.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `artworks-rest-api`: The existing requirement "Image URLs use get_media_url" needs a tighter contract — `settings.HOST` MUST be populated from `.env.{ENV}` and `get_media_url` MUST produce valid absolute URLs even when `HOST` is unset or malformed.

## Impact

- `project/settings.py` — dotenv loading behavior
- `utils/media.py` — `get_media_url` function
- `docs/django-project-setup.md` — code examples for dotenv and `get_media_url`
- No API contract changes (responses will just return correct URLs)
- No breaking changes
