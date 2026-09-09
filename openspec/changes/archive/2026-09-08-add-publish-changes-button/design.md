## Context

The Unfold admin currently uses a plain app-list home and an empty `UNFOLD["SIDEBAR"]["navigation"]` list. There is no in-admin mechanism for staff to publish/redeploy the frontend. This change adds the first of a series of **system action buttons**: a staff-visible "Publicar Cambios" sidebar entry backed by a config-driven deploy service (local success when unconfigured, real Coolify webhook POST when `DEPLOY_WEBHOOK_URL` is set).

The `core` app already exists (cross-cutting mixins/models) and is the natural home for system-wide, non-model action views. Django's messages framework is the built-in, Unfold-native way to surface success/error feedback.

```
sidebar item "Publicar Cambios"
        │ link (GET)
        ▼
   /admin/system/publish/   (core app view)
        │
        ▼
   staff-only check  ──no──▶ 403 / staff_member_required(login_url=admin)
        │ yes
        ▼
   publish_changes()   (config-driven, HTTP-shaped)
        │
        ▼
   DEPLOY_WEBHOOK_URL set?  ──no (dummy now)──▶  local success (no network)
        │ yes (later, real deploy)
        ▼
   HTTP POST to Coolify webhook + secret  →  messages success/error
        │
        ▼
   redirect to admin index
```

## Goals / Non-Goals

**Goals:**
- Give all staff users a one-click, discoverable "Publicar Cambios" button.
- Prove the full loop end to end: button → action view → dummy call → feedback → return.
- Establish a re-usable pattern that future system buttons (real redeploy webhook, etc.) can follow with minimal new code.
- Keep it simple and dependency-free for this iteration.

**Non-Goals:**
- Building a full custom dashboard home screen (`templates/admin/index.html`) — overkill for a single button; deferred until there are ~5+ actions.
- A confirmation step, async job queue (Celery), or polling for build completion.
- Per-record or object-bound actions.

## Decisions

**Decision 1: Placement — sidebar navigation, not a custom dashboard or header.**
The single button lives in `UNFOLD["SIDEBAR"]["navigation"]`, using the framework's native item rendering (title + Material icon + permission hook). Rationale: zero template/Tailwind work, permission-aware per item, scales from 1→5+ by just appending items. A custom dashboard would require the Tailwind compile pipeline — heavy for one button. The header only comfortably fits 1–3 buttons and is cramped.
- *Alternative considered:* Custom `templates/admin/index.html` dashboard. Rejected now (setup cost), kept as the growth path past ~5 actions.

**Decision 2: System action view in the `core` app, gated by `@staff_member_required`.**
A lightweight Django function view at a namespaced admin URL (e.g. `/admin/system/publish/`) protected by decorators that only allow authenticated staff. "All admin/staff users" = `is_staff=True`; access fails closed.
- *Alternative considered:* A per-model admin `action` (like the existing `@action` in `admin_base.py`). Rejected — the button is global/system-level, not bound to a single change-list or object.

**Decision 3: Single `DEPLOY_WEBHOOK_URL` env var; real POST when set, local success when unset.**
The deploy target is one setting fed by one env var: `DEPLOY_WEBHOOK_URL = os.getenv("DEPLOY_WEBHOOK_URL", "")` in `project/settings.py` (same pattern as the `STRIPE_*` block). The value holds the full Coolify URL including query params, e.g. `https://apps.darideveloper.com/api/v1/deploy?uuid=XXXX&force=false` — the uuid/token stays embedded in that value; there is no separate token var and no Authorization header.
- **Unset (empty) → dummy mode.** `publish_changes()` short-circuits to local success — no network, no secret needed. It may log the would-be action without the URL value.
- **Set → real deploy.** `publish_changes()` performs a real HTTP POST to the URL via stdlib `urllib` with a short timeout (~10s), no new dependency. Non-2xx or network error raises so the view surfaces `messages.error`. The URL value itself is never logged — log only configured/unconfigured + status code.
- *Alternative considered:* Split `COOLIFY_DEPLOY_BASE` + `COOLIFY_DEPLOY_UUID` vars with code-built query string. Rejected — user chose the single-URL var as simplest and closest to the Coolify example.
- *Alternative considered:* Bare in-process stub with no HTTP shape. Rejected — less faithful to the real call and would require reworking the service later.
- *Alternative considered:* Hitting a throwaway real URL now. Rejected — unnecessary external dependency for a placeholder.

**Decision 4: No confirmation step; click fires immediately.**
Confirmed by the user. Rationale: admin-only surface + speed. The dummy call is harmless; the real redployment will be a synchronous fire-and-forget webhook (`202`) rather than blocking.
- *Trade-off noted:* A GET link triggering a state change is not CSRF-tracked like a POST+confirm. Here the action is a harmless in-process stub, and the page is staff-only, so a GET-link is acceptable for this iteration. The later real-webhook follow-up should revisit POST+CSRF or a confirm step to be safe.
- *Alternative considered:* POST + CSRF + confirm page. Rejected now by user (no confirm, immediate), flagged as the correct upgrade for the real webhook later.

**Decision 5: Feedback via Django messages + redirect.**
The view always ends by redirecting (to `reverse("admin:index")`) and calling `messages.success(...)` / `messages.error(...)`. Unfold renders these banners natively, so the operator sees a green/red toast on the dashboard with zero custom templating.
- *Alternative considered:* Returning an HTML page with inline JS. Rejected — messages are the built-in, lowest-effort, and server-authoritative source of truth.

**Decision 6: URL routing under the admin namespace.**
Route lives in `core/urls.py` and is included under a stable path. This keeps it clearly admin-operational and easy to move if the admin grows.

## Risks / Trade-offs

- **GET link fires a side effect** → Harmless local success when unconfigured; when configured it triggers a real redeploy. The follow-up MUST move to POST + CSRF (and optionally a confirm) so a stray/browser-driven GET can't trigger an actual redeployment.
- **Secret in query string gets logged** → The uuid is embedded in `DEPLOY_WEBHOOK_URL`, so proxies/logs capture it if the full URL is logged. Mitigation: never log the URL value; log only configured/unconfigured + HTTP status.
- **Dummy call gives false confidence** → The success path is unproven against the real Coolify webhook. Mitigation: keep the service interface tiny and single-purpose so the swap is trivial and the failure path already surfaces via `messages.error`.
- **"All staff" see it but may not understand publish implications** → The button's description/text is clear ("Publicar Cambios"); if misuse becomes an issue later, restricting to superusers is a one-line permission change.
- **Permission drift (staff without deploy permission)** → For now staff == can publish by design; revisit if separate `publish` perms are ever needed (visit `core/models`/auth groups).

## Open Questions

- Should the button also show a maintenance/disabled state during an in-flight real webhook? Not needed for the dummy; decide in the real-webhook follow-up.