## 1. Deploy service + env contract

- [x] 1.0 Add `DEPLOY_WEBHOOK_URL` and `COOLIFY_API_TOKEN` (API token with `deploy` permission, sent as Bearer header) to `project/settings.py` plus placeholders to `.env.dev.example` and `.env.prod.example`
- [x] 1.1 Create `core/services/__init__.py` (if the package does not exist)
- [x] 1.2 Create `core/services/publishing.py` with a `publish_changes()` function: when `settings.DEPLOY_WEBHOOK_URL` is empty it short-circuits to local success (no network); when set it sends a GET to that URL with `Authorization: Bearer <COOLIFY_API_TOKEN>` and a neutral `User-Agent` (Cloudflare 1010 blocks Python-urllib) via stdlib `urllib` with a short timeout (~10s) and never logs URL or token values
- [x] 1.3 Ensure `publish_changes()` raises on non-2xx/network error in a way the caller can detect (so the failure message path is reachable)

## 2. Publish action view

- [x] 2.1 Add a staff-only system action view in `core/views.py` (protected by `@staff_member_required` with `login_url` pointing to the admin login) that calls `publish_changes()`
- [x] 2.2 On success, call `messages.success(...)` with "Cambios publicados correctamente, espere 5-10 minutos para verlos reflejados en la web (preferiblemente use una ventana de incógnito)" and redirect to `reverse("admin:index")`
- [x] 2.3 On failure, call `messages.error(...)` with the error detail and redirect to `reverse("admin:index")`
- [x] 2.4 Confirm the view ends with a redirect (no intermediate confirmation page)

## 3. URL routing

- [x] 3.1 Create `core/urls.py` if it does not exist and add a stable route (e.g. `system/publish/`) mapped to the view
- [x] 3.2 Include `core/urls.py` in `project/urls.py` under the admin path (`admin/system/`) so the action view sits in the admin namespace and is reachable at the URL expected by the sidebar link

## 4. Sidebar button

- [x] 4.1 Add a "Publicar Cambios" item to `UNFOLD["SIDEBAR"]["navigation"]` in `project/settings.py`, linking to the publish action URL (via `reverse_lazy`), with a Material icon
- [x] 4.2 Scope the nav item so it renders for staff users and is hidden for non-staff (permission hook on the item)
- [x] 4.3 Verify the whole flow manually: staff user clicks button → action runs → success message shows on the admin dashboard; non-staff user cannot reach the action URL directly

## 5. Tests & verification

- [x] 5.1 Add a test that a staff user reaching the publish action URL gets redirected and a success message is queued
- [x] 5.2 Add a test that a non-staff/unauthenticated user cannot trigger the action
- [x] 5.3 Add a test that the action view fails closed and surfaces an error message when `publish_changes()` raises
- [x] 5.4 Add a test with `override_settings(DEPLOY_WEBHOOK_URL="https://example.test/deploy?uuid=x&force=false", COOLIFY_API_TOKEN="tok")` and a mocked `urllib` POST proving the configured path hits the URL with the Bearer header without logging URL or token; add a missing-token clear-error test and a 403-hint test
- [x] 5.5 Run the test suite (and Django `check`) to confirm the change passes with no regressions