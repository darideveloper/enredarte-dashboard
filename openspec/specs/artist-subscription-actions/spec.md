## Requirements

### Requirement: Generate subscription link action
The system SHALL provide a "Generar link de suscripción" changeform action on the Artist admin change page that creates a Stripe customer and checkout session when no subscription link has been generated yet. The action SHALL be visible only when the artist has no `signup_url` at all (no subscription or empty `signup_url`).

#### Scenario: Generate link for artist without a link
- **WHEN** an administrator opens an Artist change form and no subscription link exists (no subscription or empty `signup_url`)
- **THEN** the "Generar link de suscripción" action SHALL be shown and, when clicked, SHALL create a Stripe customer (if needed), create a checkout session, store the `signup_url` and `signup_url_expires_at`, set `status` to `PENDING`, and redirect back to the change form

#### Scenario: Generate link blocked by missing email
- **WHEN** an administrator clicks "Generar link de suscripción" for an artist with no email address
- **THEN** the system SHALL display an error message and redirect back to the change form without creating a subscription

#### Scenario: Generate link blocked by inactive billing plan
- **WHEN** an administrator clicks "Generar link de suscripción" when the `BillingPlan` has `is_active_for_new_signups` set to `False` or no `stripe_price_id`
- **THEN** the system SHALL display an error message and redirect back to the change form without creating a subscription

#### Scenario: Generate link hidden when a link exists
- **WHEN** an administrator opens an Artist change form and a `signup_url` exists (valid or expired)
- **THEN** the "Generar link de suscripción" action SHALL be hidden

### Requirement: Copy subscription link button
The system SHALL provide a "Copiar link" button on the Artist admin change page when a valid (non-expired) `signup_url` exists. The button SHALL render the URL in a `data-copy-url` attribute and copy it to the clipboard when clicked (a user gesture), without any server round-trip.

#### Scenario: Copy button shown with preloaded link
- **WHEN** an administrator opens an Artist change form and a valid (non-expired) `signup_url` exists
- **THEN** a "Copiar link" button SHALL be shown with the `signup_url` preloaded in its `data-copy-url` attribute, and the "Generar link de suscripción" button SHALL NOT be shown

#### Scenario: Copy button hidden without a valid link
- **WHEN** an administrator opens an Artist change form with no subscription, no `signup_url`, or an expired `signup_url`
- **THEN** the "Copiar link" button SHALL NOT be shown

#### Scenario: Clicking copy writes to clipboard
- **WHEN** an administrator clicks the "Copiar link" button
- **THEN** the `data-copy-url` value SHALL be written to the clipboard and the button label SHALL briefly display "¡Copiado!" without removing the button icon

### Requirement: Regenerate subscription link action
The system SHALL provide a "Regenerar link" changeform action on the Artist admin change page that reuses a valid existing checkout URL or creates a new one when expired. The action SHALL be visible whenever a subscription link exists (`signup_url` present, valid or expired).

#### Scenario: Regenerate link reuses valid URL
- **WHEN** an administrator clicks "Regenerar link" and the existing `signup_url` has not expired
- **THEN** the system SHALL reuse the existing URL without calling the Stripe checkout API and redirect back to the change form

#### Scenario: Regenerate link creates fresh session when expired
- **WHEN** an administrator clicks "Regenerar link" and the existing `signup_url` has expired
- **THEN** the system SHALL create a new checkout session, update the `signup_url` and `signup_url_expires_at`, and redirect back to the change form

### Requirement: Open customer portal action
The system SHALL provide an "Abrir Customer Portal" changeform action on the Artist admin change page that creates a Stripe billing portal session. The action SHALL be visible whenever a subscription link exists (`signup_url` present).

#### Scenario: Open portal returns portal URL
- **WHEN** an administrator clicks "Abrir Customer Portal" for an artist with a subscription link and a `stripe_customer_id`
- **THEN** the system SHALL create a Stripe billing portal session and show the portal URL in a success message

#### Scenario: Open portal blocked without customer
- **WHEN** an administrator clicks "Abrir Customer Portal" for an artist with a subscription link but no `stripe_customer_id`
- **THEN** the system SHALL display a warning message and redirect back to the change form

### Requirement: Sync from Stripe action
The system SHALL provide a "Sincronizar desde Stripe" changeform action on the Artist admin change page that re-fetches the customer and subscription state from the Stripe API and updates the local `ArtistSubscription` and `Artist.is_active` accordingly. The action SHALL always be visible.

#### Scenario: Sync updates subscription state
- **WHEN** an administrator clicks "Sincronizar desde Stripe" for an artist with a `stripe_customer_id`
- **THEN** the system SHALL fetch the customer and subscriptions from Stripe, update the local `ArtistSubscription` fields, recompute `Artist.is_active`, and redirect with a success message showing the status change

#### Scenario: Sync without customer shows warning
- **WHEN** an administrator clicks "Sincronizar desde Stripe" for an artist without a `stripe_customer_id`
- **THEN** the system SHALL display a warning message and redirect back to the change form

### Requirement: Unfold-native horizontal button layout
The system SHALL render all server actions using Unfold's `actions_detail` API and the copy button as a single horizontal header item, with no vertical stacking or header overflow.

#### Scenario: Buttons render horizontally
- **WHEN** an administrator opens an Artist change form
- **THEN** the subscription buttons SHALL appear as horizontal items in the Unfold header area, not as vertically stacked forms

#### Scenario: Conditional visibility via permission methods
- **WHEN** an administrator opens an Artist change form
- **THEN** only the applicable buttons SHALL be shown based on the artist's subscription state — no link: generate + sync; link exists: regenerate + portal + sync; valid (non-expired) link additionally shows the copy button — enforced via `@action(permissions=[...])` and `has_<action>_permission` methods