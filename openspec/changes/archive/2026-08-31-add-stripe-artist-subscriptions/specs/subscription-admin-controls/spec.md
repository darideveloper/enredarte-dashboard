## ADDED Requirements

### Requirement: Subscription admin endpoints gated by staff
The system SHALL expose admin-only HTTP endpoints for subscription control. Each endpoint MUST require `request.user.is_staff` and MUST be reachable from the Django admin change_view only.

#### Scenario: Non-staff request rejected
- **WHEN** a request without `is_staff=True` reaches any subscription admin endpoint
- **THEN** the system SHALL return HTTP 403 (or redirect to admin login) and SHALL NOT execute the underlying business logic.

#### Scenario: Staff request accepted
- **WHEN** a staff member reaches a subscription admin endpoint
- **THEN** the system SHALL execute the action and return to the artist change page with the updated state.

### Requirement: Generate subscription link endpoint
The system SHALL expose `POST /subscriptions/admin/artists/<artist_id>/generate-link/` which, when called by a staff member, creates a Stripe Customer with `email = Artist.email`, creates a Stripe Checkout Session in `subscription` mode using `BillingPlan.stripe_price_id` with `metadata={"artist_id": <id>}` and `success_url` / `cancel_url` pointing at `/subscriptions/success/` and `/subscriptions/cancel/`, and persists the resulting `signup_url` and `signup_url_expires_at` on the `ArtistSubscription` row. The endpoint SHALL redirect back to the artist change page (so the operator can use the "Copiar link" button to share the new URL) and SHALL show a Django admin success message confirming the link was generated.

#### Scenario: First link for an artist
- **WHEN** a staff member clicks "Generar link de suscripción" for an `Artist` who has no `ArtistSubscription` yet
- **THEN** the system SHALL create the artist subscription row with `status="pending"`, persist the Stripe customer and session URL, set the artist `is_active=False` via `compute_is_active` (a pending, unpaid artist is not yet visible on the public site), redirect back to the artist change page, and show a Django admin success message. The "Copiar link" button SHALL be visible on the next page load with the new `signup_url` preloaded in its `data-copy-url` attribute so the operator can share it with the artist.

#### Scenario: Artist has no email
- **WHEN** a staff member triggers "Generar link de suscripción" for an `Artist` whose `email` is empty
- **THEN** the system SHALL NOT call the Stripe API and SHALL show the admin message ("Este artista no tiene un correo electrónico. Captura uno antes de generar el link.").

### Requirement: Reuse the existing copy-to-clipboard helper
The system SHALL reuse the project's existing copy-to-clipboard pattern (`static/js/copy_clipboard.js`, the `[data-copy-url]` attribute selector) to expose the Stripe Checkout Session URL to the operator from the artist change page. The implementation pattern is: render an Unfold action button labelled "Copiar link" in the change-form header with the current `signup_url` preloaded in a `data-copy-url` attribute, and let `copy_clipboard.js` write the URL to the clipboard on a user click (a real user gesture — the Clipboard API requires it). No server round-trip and no `copy_to_clipboard` cookie are involved.

#### Scenario: Copy button shown with preloaded link
- **WHEN** a staff member opens an `Artist` change page and a non-expired `signup_url` exists
- **THEN** a "Copiar link" button SHALL be rendered in the change-form actions bar with the `signup_url` preloaded in its `data-copy-url` attribute; the existing `copy_clipboard.js` SHALL write that value to the clipboard when the operator clicks the button.

#### Scenario: Copy button hidden without a valid link
- **WHEN** a staff member opens an `Artist` change page with no `ArtistSubscription`, an empty `signup_url`, or an expired `signup_url`
- **THEN** the "Copiar link" button SHALL NOT be rendered.

#### Scenario: Clicking copy writes to clipboard with visual confirmation
- **WHEN** a staff member clicks the "Copiar link" button
- **THEN** the `data-copy-url` value SHALL be written to the clipboard and the button label SHALL briefly display "¡Copiado!" (driven by `copy_clipboard.js`).

#### Scenario: No server round-trip required to copy
- **WHEN** the copy button is rendered
- **THEN** the operator MUST be able to copy the URL with a single click; the page MUST NOT require any extra "right-click → copy", cookie, or follow-up request to expose the URL.

### Requirement: Regenerate subscription link endpoint
The system SHALL expose `POST /subscriptions/admin/artists/<artist_id>/regenerate-link/` which creates a fresh Stripe Checkout Session for an artist whose previous signup URL has expired or been used, and replaces `signup_url` / `signup_url_expires_at` on the `ArtistSubscription` row.

#### Scenario: Regenerating an expired link
- **WHEN** a staff member clicks "Regenerar link de suscripción" for an artist whose `signup_url_expires_at` is in the past
- **THEN** the system SHALL create a new Stripe Checkout Session with the SAME `stripe_customer_id` already stored, persist the new URL, and SHALL NOT modify `stripe_subscription_id` or `status`.

#### Scenario: Regenerating before payment
- **WHEN** a staff member regenerates a link for an artist in status `pending`
- **THEN** the system SHALL reuse the existing `stripe_customer_id`, reset `signup_url_expires_at`, and keep `status="pending"`.

### Requirement: Open Customer Portal endpoint
The system SHALL expose `POST /subscriptions/admin/artists/<artist_id>/open-portal/` which creates a Stripe Customer Portal session for the artist's stored `stripe_customer_id` and returns its URL to the admin so the operator can share it with the artist (copy-paste or "send by email" button).

#### Scenario: Generating a portal URL
- **WHEN** a staff member clicks "Abrir Customer Portal" for an artist whose `ArtistSubscription` already has `stripe_customer_id`
- **THEN** the system SHALL create a Stripe Billing Portal session for that customer, display its URL in the admin, and return the operator to the artist change page.

#### Scenario: Generating a portal URL for an artist not yet subscribed
- **WHEN** a staff member clicks "Abrir Customer Portal" for an artist whose `ArtistSubscription` has no `stripe_customer_id`
- **THEN** the system SHALL show the admin warning ("Aún no se generó un link de pago para este artista.") and SHALL NOT call the Stripe Billing Portal API.

### Requirement: Sync from Stripe endpoint
The system SHALL expose `POST /subscriptions/admin/artists/<artist_id>/sync-from-stripe/` which fetches the latest customer and subscription state from the Stripe API and updates the local `ArtistSubscription` row + `Artist.is_active` via `compute_is_active`.

#### Scenario: Sync corrects a missed webhook
- **WHEN** a staff member clicks "Sincronizar desde Stripe" for an artist whose local state is older than what Stripe reports
- **THEN** the system SHALL update `status`, `current_period_end`, `cancel_at_period_end` to match Stripe, persist the resulting `Artist.is_active`, update `last_synced_at`, and show a success message including the previous vs new `status`.

#### Scenario: Sync warns for never-subscribed artist
- **WHEN** a staff member clicks "Sincronizar desde Stripe" for an artist with no `stripe_customer_id`
- **THEN** the system SHALL show the admin warning ("Este artista aún no tiene un customer en Stripe.") and SHALL NOT call the Stripe API.

### Requirement: Success and cancel landing endpoints
The system SHALL expose `GET /subscriptions/success/?session_id=...` and `GET /subscriptions/cancel/` as lightweight landing pages that simply show a confirmation message in Spanish (and English by `Accept-Language`). They MUST NOT perform any Stripe API call and MUST NOT depend on cookies or other client state.

#### Scenario: Successful checkout landing
- **WHEN** a buyer lands on `/subscriptions/success/?session_id=...` after paying
- **THEN** the page SHALL display "¡Gracias! Tu suscripción está activa." ("Thanks! Your subscription is active.") and a hint that the artist's visibility on the public site is automatic once payment is confirmed.

#### Scenario: Cancelled checkout landing
- **WHEN** a buyer lands on `/subscriptions/cancel/` from an abandoned checkout
- **THEN** the page SHALL display "Tu pago fue cancelado. Puedes intentarlo nuevamente cuando quieras." and SHALL NOT make any API call.

### Requirement: Portal return landing endpoint
The system SHALL expose `GET /subscriptions/portal-return/` as a neutral landing page shown after the artist leaves the Stripe Customer Portal, and SHALL use its URL as the portal session `return_url`. The page MUST NOT claim the subscription is active, because the artist may have just cancelled, updated their card, or viewed invoices.

#### Scenario: Landing after leaving the portal
- **WHEN** an artist lands on `/subscriptions/portal-return/` after leaving the Customer Portal
- **THEN** the page SHALL display a generic message ("Gracias por usar el portal de gestión." / "Thanks for using the management portal.") and SHALL NOT perform any Stripe call.

### Requirement: ArtistSubscription admin registration
The system SHALL register `ArtistSubscription` in the Django Unfold admin so an operator can browse and search subscriptions: list by `artist`, filter by `status` (`pending`/`active`/`past_due`/`canceling`/`canceled`), filter by `is_active_of_artist` and show `created_at` / `last_synced_at`. The admin MUST support searching by `artist__name` and `stripe_subscription_id`.

#### Scenario: Filtering subscriptions by status
- **WHEN** an administrator opens the "Suscripciones de artistas" admin and selects a `status` filter
- **THEN** only `ArtistSubscription` rows in that status SHALL be shown.

#### Scenario: Searching for an artist by subscription id
- **WHEN** an administrator types a Stripe subscription id in the admin search box
- **THEN** the `ArtistSubscription` row with that `stripe_subscription_id` SHALL be the only row that matches.

### Requirement: StripeEvent admin registration
The system SHALL register `StripeEvent` in the Django Unfold admin so an operator can browse the audit log: read-only list ordered by `received_at` desc, with a date filter and `event_type` filter, and a detail view showing the `payload` JSON.

#### Scenario: Browsing recent webhook deliveries
- **WHEN** an administrator opens the "Eventos de Stripe" admin
- **THEN** rows MUST be ordered desc by `received_at`, MUST be read-only, and MUST show `event_type`, a short prefix of `event_id`, and `processed_at` (or `error` if any).

#### Scenario: Inspecting a failure
- **WHEN** an administrator opens a `StripeEvent` row whose `error` is non-empty
- **THEN** the change view SHALL show `error` and `payload` so the operator can diagnose the failure.
