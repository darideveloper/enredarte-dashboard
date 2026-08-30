## MODIFIED Requirements

### Requirement: Open customer portal action
The system SHALL provide an "Abrir Customer Portal" changeform action on the Artist admin change page that creates a Stripe billing portal session. The action SHALL be visible whenever a subscription link exists (`signup_url` present).

#### Scenario: Open portal redirects to portal URL in new tab
- **WHEN** an administrator clicks "Abrir Customer Portal" for an artist with a subscription link and a `stripe_customer_id`
- **THEN** the system SHALL create a Stripe billing portal session and redirect the browser to the portal URL in a new browser tab, keeping the admin on the current change form

#### Scenario: Open portal blocked without customer
- **WHEN** an administrator clicks "Abrir Customer Portal" for an artist with a subscription link but no `stripe_customer_id`
- **THEN** the system SHALL display a warning message and redirect back to the change form
