## Why

Local development needs a stable, public HTTPS URL so external services (e.g. Stripe webhooks) can reach the Django app. `portless` only provides a `*.localhost` subdomain, which is not publicly routable. A Cloudflare tunnel exposes the running app through a real domain, but today it must be started manually and separately from `dev.sh`.

This change makes `./dev.sh` automatically start a named Cloudflare tunnel as a tmux window alongside Django, reusing the same dynamic `runserver` port — so the project is reachable at a stable public URL the moment development starts.

## What Changes

- Extend `dev.sh` to detect `cloudflared` and, when a tunnel is configured, launch it as a dedicated tmux window (`tunnel`) pointing at the dynamic Django port.
- Generate the per-run tunnel config dynamically (hostname + `http://localhost:$PORT`, plus a required catch-all `http_status:404` rule) so the existing port-conflict avoidance is preserved.
- Resolve the tunnel credentials file at runtime from `cloudflared tunnel list` instead of hardcoding a UUID path.
- Add `CLOUDFLARE_TUNNEL_NAME` and `CLOUDFLARE_TUNNEL_HOST` to `.env.dev` / `.env.dev.example`, and include the public tunnel host in `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`, and `CSRF_TRUSTED_ORIGINS`.
- `dev.sh` reads tunnel config from `.env.dev` (via safe `grep`, no `source`) with optional environment override; it degrades gracefully when `cloudflared` or the config is absent.
- Document a security note: the tunnel makes `runserver` publicly reachable, so Cloudflare Access (zero-trust) is recommended.

## Capabilities

### New Capabilities
- `cloudflare-tunnel`: Auto-start and manage a named Cloudflare tunnel for local Django development from `dev.sh`, including env-driven configuration, dynamic port mapping, and graceful no-op when unconfigured.

### Modified Capabilities
<!-- No existing spec-level requirements change. -->

## Impact

- `dev.sh`: new tunnel bootstrap block; no change to existing Django/portless windows.
- `.env.dev`, `.env.dev.example`: two new vars + extended host lists.
- `project/settings.py`: no code change (already env-driven); only env values change.
- Dependencies: requires `cloudflared` CLI installed locally and a one-time `cloudflared tunnel login` / `create` / `route dns` (documented, not automated).
- No production, API, or data-model impact.
