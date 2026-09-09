---
created: 2026-09-09
updated: 2026-09-09
tags:
  - enredarte
  - deploy
  - coolify
  - env
type: guide
status: active
---

# Enredarte Deploy

How this project ships to Coolify and how the publish flow works. All values below are env names; real values live in gitignored `.env` files or the deploy secrets manager.

## Targets

| Target | Host | Notes |
|---|---|---|
| Production dashboard | `https://dashboard.enredarte.mx` | Django + Gunicorn on port 80 in Docker, behind Coolify |
| Landing (separate repo) | `https://enredarte.mx` | Consumes dashboard APIs at build time |

## Publish flow (`core`)

`admin/system/publish/` (`core:publish-changes`, sidebar **Sistema → Publicar Cambios**, staff-only) triggers a Coolify redeploy via two env vars in `project/settings.py`:

- `DEPLOY_WEBHOOK_URL` — single Coolify deploy webhook URL (uuid/token params included)
- `COOLIFY_API_TOKEN` — API token with `deploy` permission, sent as Bearer auth

## Environment selector

`.env` carries only `ENV=dev|prod`. Everything else lives in `.env.dev` / `.env.prod` (templates: `.env.dev.example` / `.env.prod.example`). Key groups:

| Group | Keys |
|---|---|
| Core | `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `HOST`, `DB_ENGINE/NAME/USER/PASSWORD/HOST/PORT`, `STORAGE_AWS` |
| Stripe | `STRIPE_SECRET_KEY`, `STRIPE_PUBLISHABLE_KEY`, `STRIPE_WEBHOOK_SECRET`, `STRIPE_API_VERSION`, `STRIPE_PRICE_ID` (seed only) |
| Deploy | `DEPLOY_WEBHOOK_URL`, `COOLIFY_API_TOKEN` |
| Tunnel (dev) | `CLOUDFLARE_TUNNEL_NAME`, `CLOUDFLARE_TUNNEL_HOST` |
| Storage (prod) | `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_STORAGE_BUCKET_NAME`, `AWS_PROJECT_FOLDER`, `AWS_S3_REGION_NAME`, `AWS_S3_ENDPOINT_URL`, `AWS_S3_CUSTOM_DOMAIN` |

Derived (no env): `STRIPE_SUCCESS_URL` / `STRIPE_CANCEL_URL` (from `HOST`), `STRIPE_PORTAL_RETURN_URL` (`{HOST}/subscriptions/portal-return/`).

## Docker / start.sh

- `Dockerfile` installs deps, runs `collectstatic`, exposes 80, ends with `CMD ["./start.sh"]`. Pass `SECRET_KEY`, DB, CORS/CSRF, `HOST`, Stripe, deploy, tunnel, storage vars as build args when referenced at build time.
- `start.sh` (runtime): `makemigrations --noinput` → `migrate --noinput` → `base_loaddata` → Gunicorn. Never runs `seed_loaddata` (one-time manual data).

## Live webhook

Production Stripe endpoint: `https://dashboard.enredarte.mx/webhooks/stripe/` (HTTPS, public). Copy its `whsec_...` into `STRIPE_WEBHOOK_SECRET`. See [[testing-stripe\|Testing Stripe Subscriptions]] §5.

## See also

- [[enredarte-overview\|Enredarte Overview]]
- [[django-project-setup\|Project Setup Guide]] §14 (Dockerfile/start.sh reference)
- [[django-cloudflare-tunnel\|Cloudflare Tunnel]] (dev tunnel)
