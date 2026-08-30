---
created: 2026-08-30
updated: 2026-08-30
tags:
  - django
  - dev-ops
  - cloudflare
  - tunnel
  - tmux
  - documentation
type: resource
status: active
---

# Cloudflare Tunnel for Local Django Development

This document describes how to integrate a **Cloudflare Tunnel** into the existing `dev.sh` workflow, so local Django development is exposed over a stable public HTTPS URL alongside the `portless` subdomain. The tunnel starts automatically as a `tmux` window whenever `dev.sh` launches the project.

## 🚀 Overview

The existing `dev.sh` (see [[django-local-subdomain-setup|Local Development & Subdomain Setup]]) starts Django behind `portless` on a `*.localhost` subdomain — great for browser work, but not reachable from the internet. External services (Stripe webhooks, OAuth callbacks, third-party APIs) need a real public URL.

A Cloudflare tunnel (`cloudflared`) solves this by routing traffic from a public hostname (e.g. `project-name.your-domain.com`) to `localhost:PORT` without port-forwarding or firewall rules. This guide integrates that into `dev.sh` so the tunnel starts as a tmux window next to Django — no separate manual step.

**What you get after following this guide:**

| Local | Public |
|-------|--------|
| `https://project-name.localhost` (portless) | `https://project-name.your-domain.com` (cloudflare tunnel) |

Both point to the same Django `runserver` instance on the same dynamic port.

## 📦 Prerequisites

Install the following on the development machine:

- **`cloudflared`** (≥ 2022.x, any recent version): Cloudflare's tunnel client. Install via `brew install cloudflared` (macOS) or `apt install cloudflared` (Linux). Verify with `cloudflared --version`.
- **`tmux`**: Terminal multiplexer (already required by `dev.sh`).
- **`portless`**: Local proxy (already required by `dev.sh`).
- **A Cloudflare-managed domain**: You need a domain added to a Cloudflare account (free tier works).
- **`python3`**: Used at runtime to parse `cloudflared tunnel list` output (already available in most Django dev environments).

## 🔧 Step 1: One-Time Cloudflare Setup

These commands run **once per developer machine**. Each team member must run these steps on their own machine — the tunnel credentials and DNS are local to each environment. After this, `dev.sh` handles everything automatically.

### 1.1 Authenticate

```bash
cloudflared tunnel login
```

This opens a browser. Log in to Cloudflare and authorize the tunnel. A certificate is saved to `~/.cloudflared/cert.pem`.

### 1.2 Create a Named Tunnel

```bash
cloudflared tunnel create <project-name>-dev
```

Replace `<project-name>` with your Django project directory name (e.g. `my-project-dev`). The command prints a UUID and saves credentials to `~/.cloudflared/<UUID>.json`.

### 1.3 Route DNS

```bash
cloudflared tunnel route dns <project-name>-dev <project-name>.your-domain.com
```

This creates a CNAME record in your Cloudflare DNS zone pointing `<project-name>.your-domain.com` to the tunnel.

**Note:** If `cloudflared tunnel route dns` routes to the wrong tunnel (a known issue), create the CNAME record manually in the Cloudflare Dashboard or via the Cloudflare API:
- Type: CNAME
- Name: `<project-name>`
- Target: `<TUNNEL-UUID>.cfargotunnel.com`
- Proxy status: Proxied (orange cloud)

## ⚙️ Step 2: Environment Variables

Add two variables to `.env.dev` (and `.env.dev.example` for team onboarding). In a fresh project, copy `.env.dev.example` to `.env.dev` first.

```env
# Cloudflare Tunnel
CLOUDFLARE_TUNNEL_NAME=<project-name>-dev
CLOUDFLARE_TUNNEL_HOST=<project-name>.your-domain.com
```

Also append the tunnel host to the existing allow-lists so Django accepts requests through the tunnel:

```env
ALLOWED_HOSTS=localhost,127.0.0.1,<project-name>.localhost,<project-name>.your-domain.com
CORS_ALLOWED_ORIGINS=https://<project-name>.localhost,https://<project-name>.your-domain.com
CSRF_TRUSTED_ORIGINS=https://<project-name>.localhost,https://<project-name>.your-domain.com
```

**No `settings.py` change is needed** — the project already reads `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`, and `CSRF_TRUSTED_ORIGINS` from environment variables (see [[django-local-subdomain-setup|Local Development & Subdomain Setup]] Step 1).

## 📜 Step 3: `dev.sh` Integration

Add the following block to `dev.sh` **after** the Django `tmux new-session` and **before** `tmux select-window` / `tmux attach`. This placement ensures the tunnel only starts on the first `dev.sh` launch (when the session is created), matching how Django itself is handled.

```bash
# --- Cloudflare Tunnel (auto-start) ---
# SECURITY: The tunnel makes runserver publicly reachable over HTTPS.
# For dev-only use; consider Cloudflare Access (zero-trust) in front of
# the hostname so only you can reach it.
cf_env() { grep -E "^$1=" .env.dev 2>/dev/null | head -1 | cut -d= -f2-; }
CF_NAME="${CLOUDFLARE_TUNNEL_NAME:-$(cf_env CLOUDFLARE_TUNNEL_NAME)}"
CF_HOST="${CLOUDFLARE_TUNNEL_HOST:-$(cf_env CLOUDFLARE_TUNNEL_HOST)}"

if command -v cloudflared >/dev/null 2>&1 && [ -n "$CF_NAME" ] && [ -n "$CF_HOST" ]; then
  CF_ID=$(cloudflared tunnel list -o json 2>/dev/null \
    | python3 -c "import sys,json; d=json.load(sys.stdin); print(next(t['id'] for t in d if t.get('name')=='$CF_NAME'))")
  CF_CRED="$HOME/.cloudflared/$CF_ID.json"
  CF_CONFIG="$HOME/.cloudflared/config-${PROJECT_NAME}.yml"
  cat > "$CF_CONFIG" <<YML
tunnel: $CF_NAME
credentials-file: $CF_CRED
ingress:
  - hostname: $CF_HOST
    service: http://localhost:$PORT
  - service: http_status:404
YML
  tmux new-window -n 'tunnel' -c "$PWD" \
    "bash -c 'cloudflared tunnel --config $CF_CONFIG run $CF_NAME; read'"
fi
```

### How It Works

| Line | Purpose |
|------|---------|
| `cf_env()` | Extracts a key from `.env.dev` via `grep` — avoids `source`-ing the file (which breaks on `SECRET_KEY` characters like `()`). |
| `CF_NAME` / `CF_HOST` | Resolved from shell environment first, falling back to `.env.dev`. |
| `command -v cloudflared` | If `cloudflared` is not installed or either var is empty, the entire block is skipped — `dev.sh` behaves exactly as before. |
| `cloudflared tunnel list -o json` | Resolves the tunnel UUID at runtime so no machine-specific path is hardcoded. |
| `config-<project>.yml` | Generated per-run with the correct `$PORT` and a mandatory catch-all `http_status:404` (required by `cloudflared`). |
| `bash -c '...; read'` | Keeps the tmux window open if the tunnel exits, so logs are inspectable. |

### Complete `dev.sh` Example

```bash
#!/bin/bash

PROJECT_NAME=$(basename "$PWD")
SESSION_NAME="${PROJECT_NAME}_dev"

if tmux has-session -t $SESSION_NAME 2>/dev/null; then
    echo "Session $SESSION_NAME already exists. Attaching..."
    tmux attach -t $SESSION_NAME
    exit 0
fi

portless proxy start
portless trust

PORT=8000
while ss -tuln | grep -q ":$PORT " ; do
    PORT=$((PORT+1))
done

VENV_CMD=""
[ -d "venv" ] && VENV_CMD="source venv/bin/activate && "
[ -d ".venv" ] && VENV_CMD="source .venv/bin/activate && "

tmux new-session -d -s $SESSION_NAME -n 'django' -c "$PWD" \
    "bash -c '${VENV_CMD}portless $PROJECT_NAME --app-port $PORT -- python manage.py runserver $PORT; read'"

# --- Cloudflare Tunnel (auto-start) ---
# SECURITY: The tunnel makes runserver publicly reachable over HTTPS.
# For dev-only use; consider Cloudflare Access (zero-trust) in front of
# the hostname so only you can reach it.
cf_env() { grep -E "^$1=" .env.dev 2>/dev/null | head -1 | cut -d= -f2-; }
CF_NAME="${CLOUDFLARE_TUNNEL_NAME:-$(cf_env CLOUDFLARE_TUNNEL_NAME)}"
CF_HOST="${CLOUDFLARE_TUNNEL_HOST:-$(cf_env CLOUDFLARE_TUNNEL_HOST)}"

if command -v cloudflared >/dev/null 2>&1 && [ -n "$CF_NAME" ] && [ -n "$CF_HOST" ]; then
  CF_ID=$(cloudflared tunnel list -o json 2>/dev/null \
    | python3 -c "import sys,json; d=json.load(sys.stdin); print(next(t['id'] for t in d if t.get('name')=='$CF_NAME'))")
  CF_CRED="$HOME/.cloudflared/$CF_ID.json"
  CF_CONFIG="$HOME/.cloudflared/config-${PROJECT_NAME}.yml"
  cat > "$CF_CONFIG" <<YML
tunnel: $CF_NAME
credentials-file: $CF_CRED
ingress:
  - hostname: $CF_HOST
    service: http://localhost:$PORT
  - service: http_status:404
YML
  tmux new-window -n 'tunnel' -c "$PWD" \
    "bash -c 'cloudflared tunnel --config $CF_CONFIG run $CF_NAME; read'"
fi

tmux select-window -t $SESSION_NAME:0
tmux attach -t $SESSION_NAME
```

## ✅ Step 4: Verification

1. Run `./dev.sh`. A new tmux session starts with two windows: `django` and `tunnel`.
2. Switch to the `tunnel` window (`Ctrl+b` then `n`) and confirm it shows registered connections (e.g. `Registered tunnel connection`).
3. Visit `https://<project-name>.your-domain.com` — Django loads over HTTPS.
4. With `cloudflared` absent or the tunnel vars unset, confirm `dev.sh` still starts Django/portless unchanged (the tunnel block is silently skipped).

## 🔒 Security Note

The tunnel makes `python manage.py runserver` publicly reachable over HTTPS. `runserver` is not hardened for production use. For dev-only work:

- **Cloudflare Access (zero-trust)**: Add an Access policy in front of the tunnel hostname so only authenticated users can reach it. This is free for up to 50 users.
- **Treat as short-lived**: Use the tunnel for webhook testing and OAuth callbacks, not as a permanent public endpoint.
- **No secrets in the tunnel**: The tunnel exposes whatever Django serves — do not rely on it for sensitive data in a shared environment.

## 💡 Common Use Cases

### Stripe Webhooks

With the tunnel running, point the Stripe CLI at the public URL:

```bash
stripe listen --forward-to https://<project-name>.your-domain.com/payments/webhook/
```

Or register the webhook URL directly in the Stripe Dashboard. The tunnel is now the public callback endpoint for Stripe events.

### OAuth2 Callbacks

Google, Microsoft, and other OAuth providers require a public HTTPS redirect URI. Use the tunnel hostname as the authorized redirect domain:

```
https://<project-name>.your-domain.com/accounts/callback/
```

No port forwarding or ngrok needed — Cloudflare handles TLS and DNS.

## 📋 Replicating in Other Projects

This integration is designed to drop into any Django project that uses the `dev.sh` + `tmux` + `portless` pattern (see [[django-local-subdomain-setup|Local Development & Subdomain Setup]]). To replicate:

1. Install `cloudflared` on the target machine.
2. Run the one-time setup (Step 1 above) with the new project name and domain.
3. Add `CLOUDFLARE_TUNNEL_NAME` and `CLOUDFLARE_TUNNEL_HOST` to `.env.dev` / `.env.dev.example`.
4. Append the tunnel host to `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`, and `CSRF_TRUSTED_ORIGINS`.
5. Copy the tunnel block from Step 3 into `dev.sh`, placing it after the Django `tmux new-session` and before `tmux select-window` / `tmux attach`.
6. Run `./dev.sh` and verify.

The block is self-contained — no changes to `settings.py`, no new Python dependencies, no Docker changes. It reads config from `.env.dev` and degrades gracefully when `cloudflared` or the config is absent.

## 🛠️ Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `tunnel` window shows no output | `cloudflared` not installed or vars not set | Check `command -v cloudflared` and verify `CLOUDFLARE_TUNNEL_NAME` / `CLOUDFLARE_TUNNEL_HOST` are in `.env.dev` |
| `error code: 1033` | DNS CNAME points to wrong tunnel | Verify CNAME in Cloudflare Dashboard; recreate manually if `route dns` targeted the wrong tunnel |
| Django returns 400/Bad Request | Hostname not in `ALLOWED_HOSTS` | Add the tunnel host to `ALLOWED_HOSTS` in `.env.dev` |
| CSRF verification failed | Origin not in `CSRF_TRUSTED_ORIGINS` | Add `https://<tunnel-host>` to `CSRF_TRUSTED_ORIGINS` in `.env.dev` |
| Tunnel connects but 502/530 | Django not yet bound to port | Wait a few seconds; `cloudflared` retries automatically |
| `dev.sh` doesn't start tunnel on re-attach | Expected behavior — `dev.sh` early-returns when session exists | Kill session (`tmux kill-session -t <name>`) and re-run `./dev.sh`, or start tunnel manually: `cloudflared tunnel run <name>` |

## 📚 References

- [[django-local-subdomain-setup|Local Development & Subdomain Setup]] — the `dev.sh` + `tmux` + `portless` pattern this guide extends
- `openspec/changes/archive/2026-08-30-cloudflare-tunnel-autostart/` — the formal proposal, design, specs, and task list that drove this integration (archived change)
- [Cloudflare Tunnel Documentation](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/) — official `cloudflared` reference
