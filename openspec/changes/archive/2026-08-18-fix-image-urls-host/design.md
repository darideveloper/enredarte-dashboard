## Context

The project uses `python-dotenv` to load environment-specific `.env.{ENV}` files at startup. `portless` (the dev proxy) injects `HOST=127.0.0.1` into the shell before launching Django. `load_dotenv()` defaults to not overriding existing env vars, so the `.env.dev` value (`HOST=http://enredarte.localhost`) is silently ignored. `get_media_url()` in `utils/media.py` blindly concatenates `settings.HOST` with the relative URL, producing `127.0.0.1/media/...`.

## Goals / Non-Goals

**Goals:**
- Image URLs in API responses use the `HOST` value from `.env.{ENV}`, not shell-injected vars.
- `get_media_url` produces valid absolute URLs even if `settings.HOST` is `None` or lacks a protocol.

**Non-Goals:**
- Renaming the `HOST` env var (would require changing all env files, Dockerfile, deployment configs).
- Changing the API response format or contract.

## Decisions

### 1. Use `override=True` on the env-specific dotenv load

**Decision:** Change `load_dotenv(BASE_DIR / f".env.{ENV}")` to `load_dotenv(BASE_DIR / f".env.{ENV}", override=True)`.

**Rationale:** The env-specific file (`.env.dev`, `.env.prod`) is the authoritative source for that environment's configuration. Shell-injected vars from tools like portless are incidental and should not override project-defined values. The first `load_dotenv(BASE_DIR / ".env")` stays without `override` since it only sets `ENV` (a bootstrap value).

**Alternative considered:** Rename `HOST` to `SITE_URL` to avoid collision. Rejected — more invasive (all env files, Dockerfile, deployment scripts), and `HOST` is a conventional name.

### 2. Add protocol-prefix guard in `get_media_url`

**Decision:** If `settings.HOST` is `None` or empty, fall back to an empty string (relative URL). If it lacks `://`, log a warning and return the relative URL unchanged.

**Rationale:** Defense-in-depth. Even with the dotenv fix, a misconfigured environment should not silently produce broken URLs. An empty/missing HOST producing a relative URL is more useful than `None/media/...`.

## Risks / Trade-offs

- **`override=True` overrides all shell-set env vars for the env-specific file** → Mitigated by the fact that `.env.{ENV}` is the project's own config; any intentional shell vars (like portless's HOST) are exactly the ones we want to override.
- **`get_media_url` protocol guard adds a runtime check** → Negligible cost; called only during serialization (not per-request hot path).
- **Documentation drift** → The dotenv loading snippet and `get_media_url` code example in `docs/django-project-setup.md` must be updated to reflect the new behavior.
