## Why

The editorial/ops staff currently has no way to publish the frontend after making changes — deploying is a manual, out-of-band step only the developer controls. We want a single, discoverable "Publicar Cambios" (publish changes) button inside the Unfold admin so any staff user can trigger a redeploy from the same place they edit content.

For this iteration the button calls a **config-driven deploy service**: when `DEPLOY_WEBHOOK_URL` is unset it succeeds locally (no network, dummy mode); when set it performs the real Coolify redeploy webhook POST. This proves out the placement, permissions, and user-feedback loop end to end, and establishes a reusable pattern for future system action buttons (1→5+ as the needs grow).

## What Changes

- Add an admin-visible **"Publicar Cambios"** button in the Unfold sidebar navigation, shown to **all admin/staff users** (not just superusers).
- The button links to a new **system action view** that:
  - is permission-gated to staff/admin users
  - calls the deploy service, which POSTs to the Coolify redeploy webhook when configured and short-circuits to local success when unconfigured (no secret required in dummy mode)
  - shows clear **success/error feedback** to the operator via Django's messages, then returns to the admin dashboard
- No confirmation step — one click fires the action immediately.
- Introduce a lightweight, re-usable **action-view pattern** so later system buttons slot in with minimal new code.

## Capabilities

### New Capabilities
- `publish-changes-action`: A staff-visible "Publicar Cambios" button in the Unfold sidebar that triggers a system action view, calls the config-driven deploy service (real Coolify webhook POST when `DEPLOY_WEBHOOK_URL` is set, local success otherwise), and reports success/failure back to the operator through Django messages. Scaffolds the reusable pattern for future admin system-action buttons.

### Modified Capabilities
<!-- None. No existing spec requirements change. -->

## Impact

- **`core` app**: hosts the new system action view and the dummy endpoint/service (the `core` app already exists and is the natural home for cross-cutting/system functionality).
- **`project/settings.py**: add the "Publicar Cambios" item to `UNFOLD["SIDEBAR"]["navigation"]`.
- **`project/urls.py` (or `core/urls.py`)**: route for the system action.
- **No DB changes**: this is a stateless action, no models/migrations.
- **No new dependencies**: uses Django's built-in messages framework; the real webhook POST uses stdlib `urllib` with a short timeout — no HTTP client library required. The deploy target is setting `DEPLOY_WEBHOOK_URL` fed by env (e.g. `https://apps.darideveloper.com/api/v1/deploy?uuid=XXXX&force=false`), authorized by setting `COOLIFY_API_TOKEN` (API token with `deploy` permission, sent as Bearer header) — both from env, never in code; neither value is ever logged.