## ADDED Requirements

### Requirement: Staff-visible "Publicar Cambios" button

The system SHALL display a "Publicar Cambios" button in the Unfold sidebar navigation, visible to any authenticated admin/staff user (staff is True), regardless of superuser status.

#### Scenario: Staff user sees the button
- **WHEN** an authenticated user with `is_staff=True` loads any admin page
- **THEN** the Unfold sidebar shows a "Publicar Cambios" item linking to the system publish action

#### Scenario: Non-staff user does not see the button
- **WHEN** an authenticated user with `is_staff=False` loads any admin page
- **THEN** the "Publicar Cambios" item is not rendered in the sidebar

#### Scenario: Anonymous user
- **WHEN** an unauthenticated user loads an admin page
- **THEN** they are redirected to the admin login screen as with any other admin page

### Requirement: Publish action triggers config-driven deploy service

The system SHALL provide a system action view, reached from the "Publicar Cambios" button, that is permission-gated to staff users and invokes the deploy service on each request. When no deploy webhook URL is configured the service SHALL succeed entirely in-process (no real external side effect); when configured it SHALL POST to the Coolify webhook.

#### Scenario: Staff user clicks the button
- **WHEN** a staff user navigates to the publish action URL
- **THEN** the action runs the deploy service successfully

#### Scenario: Non-staff user attempts the action directly
- **WHEN** a user without `is_staff=True` requests the publish action URL directly
- **THEN** the request is denied (403/redirect) and the deploy service is not executed

#### Scenario: Unconfigured webhook short-circuits to local success
- **WHEN** the publish action runs and no deploy webhook URL is configured
- **THEN** it short-circuits to local success without contacting any external service or requiring a secret

### Requirement: Deploy webhook configured from environment

The system SHALL read the Coolify deploy target from setting `DEPLOY_WEBHOOK_URL` fed by the `DEPLOY_WEBHOOK_URL` env var (e.g. `https://apps.darideveloper.com/api/v1/deploy?uuid=XXXX&force=false`) and authorize with setting `COOLIFY_API_TOKEN` fed by the `COOLIFY_API_TOKEN` env var (API token with `deploy` permission, sent as `Authorization: Bearer` header). The system SHALL never log the URL or token values.

#### Scenario: Configured webhook performs real GET
- **WHEN** the publish action runs and `DEPLOY_WEBHOOK_URL` is set
- **THEN** the service sends a GET to that URL with the Bearer token and a neutral `User-Agent` (Cloudflare blocks `Python-urllib/*` with error 1010) via stdlib with a short timeout, and a non-2xx or network error surfaces as an operator error message

#### Scenario: Missing token fails with a clear error
- **WHEN** the publish action runs and `DEPLOY_WEBHOOK_URL` is set but `COOLIFY_API_TOKEN` is empty
- **THEN** the operator gets an error message stating the token is unconfigured, with no request attempted

#### Scenario: Rejected auth gives an actionable hint
- **WHEN** Coolify answers 401/403
- **THEN** the operator error message tells them to verify `COOLIFY_API_TOKEN` and its `deploy` permission

#### Scenario: Secret never in code or logs
- **WHEN** any part of the deploy flow runs or logs
- **THEN** no webhook URL value, uuid, or token appears in code, templates, or log output (only configured/unconfigured state and HTTP status)

### Requirement: Operator feedback via Django messages

The system SHALL give the operator immediate feedback on the action's outcome using Django's messages framework. On success the operator SHALL be returned to the admin dashboard with a success message; if the action fails the operator SHALL be returned with an error message.

#### Scenario: Success feedback
- **WHEN** the deploy service succeeds
- **THEN** the user is redirected to the admin dashboard with a success message (e.g. "Cambios publicados correctamente, espere 5-10 minutos para verlos reflejados en la web (preferiblemente use una ventana de incógnito)")

#### Scenario: Failure feedback
- **WHEN** the deploy service raises an error
- **THEN** the user is redirected to the admin dashboard with an error message describing the failure

#### Scenario: No confirmation step
- **WHEN** a staff user clicks "Publicar Cambios"
- **THEN** the action fires immediately without an intermediate confirmation page