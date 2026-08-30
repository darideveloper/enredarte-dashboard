## 1. One-time Cloudflare setup (manual, documented)

- [x] 1.1 Install `cloudflared` locally (package manager of the OS).
- [x] 1.2 Run `cloudflared tunnel login` and authenticate in the browser.
- [x] 1.3 Create a named tunnel: `cloudflared tunnel create <project>-dev`.
- [x] 1.4 Route a DNS record: `cloudflared tunnel route dns <project>-dev enredarte-dashboard.<your-domain>` (subdomain convention mirrors `portless`: `enredarte-dashboard`).

## 2. dev.sh tunnel integration

- [x] 2.1 Add a `cf_env()` helper that extracts a key from `.env.dev` via `grep` (no `source`).
- [x] 2.2 Resolve `CLOUDFLARE_TUNNEL_NAME` / `CLOUDFLARE_TUNNEL_HOST` from shell env, falling back to `cf_env()`.
- [x] 2.3 Guard the block with `command -v cloudflared` and presence of both vars.
- [x] 2.4 Resolve the credentials file id via `cloudflared tunnel list -o json` (`python3` parse) and build `~/.cloudflared/config-<project>.yml` with: a hostname ingress whose `service: http://localhost:$PORT`, plus a required terminal catch-all ingress `service: http_status:404` (a named tunnel config is rejected by `cloudflared` without the catch-all).
- [x] 2.5 Create a `tunnel` tmux window running `cloudflared tunnel --config <cfg> run <name>` wrapped in `bash -c '...; read'`.
- [x] 2.6 Place the block after the Django `tmux new-session` and before `tmux select-window`/`attach` so it never blocks existing windows.

## 3. Environment configuration

- [x] 3.1 Add `CLOUDFLARE_TUNNEL_NAME=<project>-dev` and `CLOUDFLARE_TUNNEL_HOST=enredarte-dashboard.<your-domain>` to `.env.dev`.
- [x] 3.2 Append the tunnel host to `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`, and `CSRF_TRUSTED_ORIGINS` in `.env.dev`.
- [x] 3.3 Mirror the same additions in `.env.dev.example` (with placeholder domain, no real secrets).

## 4. Documentation & safety

- [x] 4.1 Add a short comment in `dev.sh` summarizing the one-time setup and the security note (recommend Cloudflare Access / treat as short-lived).

## 5. Verification

- [x] 5.1 Run `./dev.sh`; confirm a `tunnel` tmux window exists (`tmux ls` / attach).
- [x] 5.2 Confirm `cloudflared tunnel info <name>` shows active edge connections.
- [x] 5.3 Open `https://enredarte-dashboard.<your-domain>` and confirm the Django app loads over HTTPS.
- [x] 5.4 With `cloudflared` absent or vars unset, confirm `dev.sh` still starts Django/portless unchanged.
