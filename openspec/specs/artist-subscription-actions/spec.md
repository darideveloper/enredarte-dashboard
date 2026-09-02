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

#### Scenario: Open portal redirects to portal URL in new tab
- **WHEN** an administrator clicks "Abrir Customer Portal" for an artist with a subscription link and a `stripe_customer_id`
- **THEN** the system SHALL create a Stripe billing portal session and redirect the browser to the portal URL in a new browser tab, keeping the admin on the current change form

#### Scenario: Open portal blocked without customer
- **WHEN** an administrator clicks "Abrir Customer Portal" for an artist with a subscription link but no `stripe_customer_id`
- **THEN** the system SHALL display a warning message and redirect back to the change form

### Requirement: Sync from Stripe action
The system SHALL provide a "Sincronizar desde Stripe" changeform action on the Artist admin change page that re-fetches the customer and subscription state from the Stripe API and updates the local `ArtistSubscription` and `Artist.is_active` accordingly. The action SHALL always be visible. The implementation MUST handle the Stripe SDK `ListObject` shape (`Subscription.list` returns `ListObject` with `.data`, not a plain `list`) so the action succeeds for both customers with and without subscriptions, MUST handle Stripe v15 `StripeObject` without `dict.get` via `sget`/`to_plain_dict`, and MUST handle `Decimal` payloads via `to_dict(for_json=True)`.

#### Scenario: Sync updates subscription state
- **WHEN** an administrator clicks "Sincronizar desde Stripe" for an artist with a `stripe_customer_id` whose `Subscription.list` returns a `ListObject` with one active subscription (including a `StripeObject` with blocked `.get` and `Decimal`)
- **THEN** the system SHALL fetch the customer and `ListObject`, extract the subscription from `ListObject.data[0]` via `sget`/`to_plain_dict`, update the local `ArtistSubscription` fields via `apply_stripe_payload` (using `sget` and `to_plain_dict(for_json=True)`), recompute `Artist.is_active` via `compute_is_active`, and redirect with a success message showing the status change (no `KeyError` at `stripe/_list_object.py:99`, no `AttributeError` at `_stripe_object.py:163`, no `TypeError: Decimal...`).

#### Scenario: Sync without customer shows warning
- **WHEN** an administrator clicks "Sincronizar desde Stripe" for an artist without a `stripe_customer_id`
- **THEN** the system SHALL display a warning message and redirect back to the change form without calling the Stripe API.

#### Scenario: Sync does not crash on ListObject indexing
- **WHEN** `Subscription.list` returns a `ListObject` (real SDK) for a customer with subscriptions
- **THEN** the action SHALL NOT attempt `ListObject[0]` (which raises `KeyError` at `stripe/_list_object.py:99`) and SHALL use `ListObject.data[0]` (via `subs.data if hasattr(subs,"data") else subs`) so the request returns `302` instead of `500`.

#### Scenario: Sync handles empty ListObject without crash
- **WHEN** `Subscription.list` returns a `ListObject` with `data == []` (customer exists, no subscriptions)
- **THEN** the system SHALL treat it as empty (check `not ListObject.data` / `not subs_data`) and set local `status="canceled"` without raising.

#### Scenario: Sync does not crash on StripeObject.get
- **WHEN** `ListObject.data[0]` is a `StripeObject` with blocked `dict.get` (`stripe>=15`, `stripe/_stripe_object.py:163`)
- **THEN** the action SHALL NOT call `stripe_sub.get(...)` and SHALL use `sget` (`obj[key]` then `getattr`) / `to_plain_dict`, so the request returns `302` (tested with `_make_get_blocked_subscription` and `stripe.Subscription.construct_from`).

#### Scenario: Sync handles Decimal in Stripe payload
- **WHEN** the returned subscription contains `Decimal` fields (`unit_amount_decimal`, `fx_rate`, etc.)
- **THEN** the action SHALL persist `raw_state` as `to_plain_dict(for_json=True)` with `Decimal→str` conversion, so `JSONField` save does not raise `TypeError: Object of type Decimal is not JSON serializable` at `json/encoder.py:180`.

### Requirement: Unfold-native horizontal button layout
The system SHALL render all server actions using Unfold's `actions_detail` API and the copy button as a single horizontal header item, with no vertical stacking or header overflow.

#### Scenario: Buttons render horizontally
- **WHEN** an administrator opens an Artist change form
- **THEN** the subscription buttons SHALL appear as horizontal items in the Unfold header area, not as vertically stacked forms

#### Scenario: Conditional visibility via permission methods
- **WHEN** an administrator opens an Artist change form
- **THEN** only the applicable buttons SHALL be shown based on the artist's subscription state — no link: generate + sync; link exists: regenerate + portal + sync; valid (non-expired) link additionally shows the copy button — enforced via `@action(permissions=[...])` and `has_<action>_permission` methods