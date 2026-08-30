## Context

`dev.sh` orchestrates local development with `tmux` + `portless`, starting Django on a dynamically chosen port (8000, 8001, …) to avoid conflicts. `portless` only yields `*.localhost` URLs, which are not publicly reachable, so external webhooks (Stripe) cannot call back into the local app.

A Cloudflare tunnel (`cloudflared`) can expose the local `runserver` through a stable public domain over HTTPS. Today this requires a separate, manual `cloudflared tunnel run` invocation. This design integrates that step into `dev.sh` so the tunnel comes up automatically with the dev session, mapping to whatever port Django actually bound.

Constraints:
- Must not break `dev.sh` on machines without `cloudflared` or without a tunnel configured.
- Must preserve the existing dynamic-port behavior (no fixed port).
- `.env.dev` contains a `SECRET_KEY` with shell-special characters (e.g. parentheses), so `dev.sh` MUST NOT `source` the env file; tunnel vars are extracted with `grep`.
- No production or data-model impact; `settings.py` is already env-driven.

## Goals / Non-Goals

**Goals:**
- Auto-start a named Cloudflare tunnel as a `dev.sh` tmux window.
- Map the tunnel to the same dynamic `$PORT` Django uses.
- Make configuration single-source via `.env.dev` (`CLOUDFLARE_TUNNEL_NAME`, `CLOUDFLARE_TUNNEL_HOST`) with optional shell-env override.
- Degrade gracefully (no-op) when `cloudflared` or config is missing.
- Document the security implications of exposing `runserver` publicly.

**Non-Goals:**
- Automating `cloudflared tunnel login` / `create` / `route dns` (one-time manual setup).
- systemd / launchd boot auto-start (out of scope per decision).
- Replacing `portless` or changing existing Django/portless windows.
- Hardening `runserver` itself.

## Decisions

1. **Dynamic per-run config generation** (over a static config file): write `~/.cloudflared/config-<project>.yml` at runtime containing a hostname ingress with `service: http://localhost:$PORT` and a terminal catch-all ingress `service: http_status:404`. The catch-all is mandatory — `cloudflared` refuses to run a named tunnel whose ingress list does not end in a catch-all. Rationale: keeps the existing dynamic port logic intact; a static config would hardcode a port and break multi-project use.

2. **Resolve credentials file at runtime** (over hardcoding the UUID): run `cloudflared tunnel list -o json` and select the id matching the tunnel name, building `~/.cloudflared/<id>.json`. Rationale: avoids committing/encoding a machine-specific UUID path into the repo.

3. **Read tunnel vars from `.env.dev` via `grep`** (over `source`): `.env.dev`'s `SECRET_KEY` contains characters that make `source` unsafe in `bash`. A small `cf_env()` helper extracts just the two needed keys, with optional environment override.

4. **Auto-start on dev.sh's first launch when configured** (over an opt-in flag): `dev.sh` already returns early (attach only) if its tmux session exists, so the `tunnel` window is created during the initial session setup — i.e. when the project starts. If `cloudflared` is present and both `CLOUDFLARE_TUNNEL_NAME` and `CLOUDFLARE_TUNNEL_HOST` are set at that point, the window is created; if either is missing, `dev.sh` proceeds exactly as before (graceful no-op). Re-running `./dev.sh` while the session is live will not (re)start the tunnel, which matches how Django itself is handled.

5. **`read` keeps the tmux window open** on tunnel failure so logs are inspectable instead of the window exiting immediately.

## Risks / Trade-offs

- [Risk] `runserver` is unhardened and publicly reachable through the tunnel. → Mitigation: document enabling Cloudflare Access (zero-trust) in front of the hostname; treat the tunnel as short-lived for sensitive work.
- [Risk] `cloudflared tunnel list -o json` parsing depends on `python3` and a valid `cloudflared` auth. → Mitigation: guarded by the `command -v cloudflared` check and `-o json`; if parsing fails the block is skipped (tunnel simply doesn't start) rather than aborting `dev.sh`.
- [Risk] If Django isn't up yet when the tunnel starts, origin connections fail briefly. → Mitigation: `cloudflared` connects to the Cloudflare edge immediately and retries the origin per request, so this self-heals once `runserver` binds.
- [Risk] Two projects sharing the same tunnel name conflict. → Mitigation: default name is `<PROJECT_NAME>-dev`, derived from the directory, keeping it per-project.
- [Risk] `dev.sh` early-returns (attach only) when its tmux session already exists, so the `tunnel` window is only created on the first launch, not on later `./dev.sh` invocations. → Mitigation: this matches existing Django behavior; to (re)start the tunnel independently, run `cloudflared tunnel run <name>` or start a fresh session. Documented so operators don't expect auto-start on re-attach.

## Migration Plan

1. One-time (documented, manual): `cloudflared tunnel login`, `cloudflared tunnel create <project>-dev`, `cloudflared tunnel route dns <project>-dev enredarte-dashboard.<your-domain>`.
2. Apply `dev.sh` changes and `.env.dev` additions.
3. Run `./dev.sh`; verify a `tunnel` tmux window appears and the public URL serves the app.
4. Rollback: remove the tunnel block from `dev.sh` and the two vars from `.env.dev` — fully reversible, no migrations.

## Open Questions

- Should the tunnel default hostname pattern be `<project>.localhost`-style or explicitly require a real domain? Decision: require a real domain via `CLOUDFLARE_TUNNEL_HOST`; subdomain convention mirrors `portless` (`enredarte-dashboard`).
