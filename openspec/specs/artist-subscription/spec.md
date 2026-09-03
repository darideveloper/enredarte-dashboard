# artist-subscription Specification

## Purpose
TBD - created by archiving change add-stripe-artist-subscriptions. Update Purpose after archive.
## Requirements
### Requirement: ArtistSubscription model lifecycle
The system SHALL provide an `ArtistSubscription` model with a one-to-one relationship to `Artist` (via `artist.subscription`) so each artist has at most one current subscription record. The model MUST have `verbose_name`, all field-level `verbose_name`/`help_text`, and a content-based `__str__` returning `"{artist} — {status_display}"`.

#### Scenario: Creating an ArtistSubscription for an Artist
- **WHEN** any code or operator triggers subscription creation for an `Artist` who has none
- **THEN** exactly one `ArtistSubscription` row SHALL be persisted with `status="pending"`, no Stripe identifiers, an empty `signup_url`, and `last_synced_at=now()`.

#### Scenario: Attempting a second subscription for the same artist
- **WHEN** any code attempts to save a second `ArtistSubscription` for an `Artist` that already has one
- **THEN** the database SHALL reject the write due to the unique one-to-one key.

### Requirement: ArtistSubscription status states
The system SHALL model subscription state as a `Status` TextChoices with at least: `pending`, `active`, `past_due`, `canceling`, `canceled`. Each value MUST have a Spanish `verbose_name` displayed in admin (default values: "Pendiente de pago", "Activa", "Pago fallido (en gracia)", "Cancelada, vigente hasta fin de período", "Cancelada definitivamente").

#### Scenario: Status choices surfaced in admin
- **WHEN** an administrator views the `ArtistSubscription` admin
- **THEN** the `status` column SHALL display the Spanish display label and SHALL render as a colored register badge consistent with `django-unfold` conventions.

#### Scenario: New artist subscription default
- **WHEN** an `ArtistSubscription` is created via the link-generation flow
- **THEN** `status` SHALL be set to `"pending"` until the first `customer.subscription.created` or `checkout.session.completed` webhook arrives.

### Requirement: Mirror of Stripe identifiers
The system SHALL store, for each `ArtistSubscription`: `stripe_customer_id` (unique, nullable), `stripe_subscription_id` (unique, nullable), and a `raw_state` JSON snapshot of the last Stripe object processed for debugging.

#### Scenario: Customer id assigned at link generation
- **WHEN** an operator generates a subscription link for an artist
- **THEN** the `ArtistSubscription` row SHALL persist the `cus_xxx` returned by Stripe as `stripe_customer_id`.

#### Scenario: Subscription id assigned at first charge
- **WHEN** Stripe delivers a `customer.subscription.created` event after a successful first payment
- **THEN** the matching `ArtistSubscription` SHALL have `stripe_subscription_id` set to `sub_xxx` and `status="active"`.

### Requirement: Period-end and cancellation intent tracking
The system SHALL store `current_period_end` (datetime, nullable) and `cancel_at_period_end` (boolean, default `False`) on `ArtistSubscription` so the friendly-cancellation behavior is observable from the admin without consulting Stripe.

#### Scenario: Period end updated on renewal
- **WHEN** Stripe delivers a successful monthly renewal (`invoice.payment_succeeded` for the recurring period)
- **THEN** the matching `ArtistSubscription` SHALL have `current_period_end` updated to the new period end and `status` SHALL remain `active`.

#### Scenario: Cancellation requested but artist still visible
- **WHEN** Stripe delivers a `customer.subscription.updated` event with `cancel_at_period_end=True`
- **THEN** the matching `ArtistSubscription` SHALL set `status="canceling"` and `cancel_at_period_end=True` while `Artist.is_active` SHALL remain `True` until `customer.subscription.deleted`.

### Requirement: Persistent signup URL with expiration
The system SHALL store the latest Checkout Session URL on `ArtistSubscription.signup_url`, along with its `signup_url_expires_at` (computed from Stripe's session `expires_at`), so operators always have a shareable link in the admin.

#### Scenario: First link generation
- **WHEN** an operator triggers "Generar link de suscripción"
- **THEN** the system SHALL create a Stripe Checkout Session, persist its URL on `signup_url`, set `signup_url_expires_at`, set `status="pending"`, and return the URL to the admin interface for copy-paste.

#### Scenario: Regenerating an expired or used link
- **WHEN** an operator triggers "Regenerar link de suscripción" and `signup_url_expires_at` is in the past (or no link exists)
- **THEN** the system SHALL create a fresh Stripe Checkout Session, replace `signup_url` and `signup_url_expires_at`, and NOT touch `stripe_subscription_id`.

### Requirement: is_active derivation from subscription state
The system SHALL provide a pure function `subscription_state.compute_is_active(subscription, artist=None)` that returns the canonical boolean for `Artist.is_active`. The function MUST be the single source of truth; no webhook handler or admin action SHALL attempt to derive the boolean inline.

#### Scenario: Artist without subscription
- **WHEN** `compute_is_active(None, artist=<the artist>)` is called for an `Artist` with no `ArtistSubscription`
- **THEN** the function SHALL return the artist's own `is_active` boolean unchanged (preserving any manual operator toggle).

#### Scenario: Active subscription
- **WHEN** `compute_is_active(sub)` is called for a subscription with `status="active"`
- **THEN** the function SHALL return `True`.

#### Scenario: Pending (unpaid) subscription
- **WHEN** `compute_is_active(sub)` is called for a subscription with `status="pending"` (link generated, no payment yet)
- **THEN** the function SHALL return `False`.

#### Scenario: Friendly cancellation in progress
- **WHEN** `compute_is_active(sub)` is called for a subscription with `status="canceling"` and `current_period_end` in the future
- **THEN** the function SHALL return `True`.

#### Scenario: Period ended after cancellation
- **WHEN** `compute_is_active(sub)` is called for a subscription with `status="canceled"` or for a `past_due` subscription whose `current_period_end + grace_period_days` is in the past
- **THEN** the function SHALL return `False`.

### Requirement: Re-activation on resume payment
The system SHALL automatically re-activate an artist whose subscription lapses, when the next successful payment is reported by Stripe.

#### Scenario: Lapsed artist re-enables
- **WHEN** an artist is `is_active=False` due to prior `canceled` / past-grace `past_due` and Stripe delivers `invoice.payment_succeeded` tied to the same `stripe_customer_id`
- **THEN** the system SHALL update `ArtistSubscription.status="active"`, refresh `current_period_end`, and set `Artist.is_active=True`.

#### Scenario: Already-active subscription is not double-billed
- **WHEN** Stripe delivers `invoice.payment_succeeded` for a subscription already in `status="active"`
- **THEN** the system SHALL refresh `current_period_end` and SHALL NOT trigger any visible side effects.

### Requirement: Public visibility follows subscription state
The system SHALL exclude an artist from the public API (`GET /apis/artworks/artists/`) whenever their subscription is not in a paying state — `pending` (link generated, unpaid), `canceled`, or `past_due` past its grace window — by persisting the `compute_is_active` boolean onto `Artist.is_active`, which already drives the public queryset.

#### Scenario: Lapsed artist disappears from the public API
- **WHEN** an artist's subscription becomes `canceled` (or `past_due` past the grace period) and a webhook persists `Artist.is_active=False` via `compute_is_active`
- **THEN** the artist SHALL NOT appear in `GET /apis/artworks/artists/`.

#### Scenario: Unpaid pending artist is not listed
- **WHEN** an artist has a `pending` `ArtistSubscription` (link generated, no payment) and no active subscription
- **THEN** the artist SHALL NOT appear in `GET /apis/artworks/artists/`.

### Requirement: Operator-controlled sync from Stripe
The system SHALL expose a per-subscription path that re-fetches Stripe state (Customer, Subscription, latest invoices) and updates the local `ArtistSubscription` row + `Artist.is_active` via `compute_is_active`, used as a manual salvavidas when a webhook is missed. The implementation MUST correctly handle the Stripe SDK `ListObject` return type from `Subscription.list` (accessing the subscriptions via `.data`, not via integer index on the ListObject itself) for both empty and non-empty results, MUST handle Stripe v15 `StripeObject` where `dict.get` is blocked (use `sget`/`to_plain_dict` via `obj[key]`/`getattr`, not `.get`), and MUST handle `Decimal` fields (`unit_amount_decimal` etc.) via `to_dict(for_json=True)` + `Decimal→str` so `JSONField` storage never raises `TypeError: Object of type Decimal is not JSON serializable`. When the customer holds zero subscriptions, the system SHALL NOT unconditionally mark a `PENDING` subscription as `CANCELED`; the empty-list → `CANCELED` transition SHALL apply only when the local `status != PENDING` (YAGNI guard).

#### Scenario: Manual sync reconciles state
- **WHEN** an operator clicks "Sincronizar desde Stripe" on an artist with `stripe_customer_id` whose customer holds an active subscription (including a `StripeObject` whose `.get` is blocked and whose payload contains `Decimal`)
- **THEN** the system SHALL call the Stripe API for the customer and `Subscription.list(customer, limit=1)`, read the first subscription from the `ListObject`'s `data` array, replace matching fields on `ArtistSubscription` via `sget`/`to_plain_dict(for_json=True)` (`apply_stripe_payload`), run `compute_is_active`, persist the resulting boolean to `Artist.is_active`, and update `last_synced_at` and `raw_state` as JSON-serializable plain `dict`.

#### Scenario: Manual sync for a never-subscribed artist
- **WHEN** an operator clicks "Sincronizar desde Stripe" but the artist has no `stripe_customer_id`
- **THEN** the system SHALL show an admin warning ("Este artista aún no tiene suscripción en Stripe.") and SHALL NOT call the Stripe API.

#### Scenario: Manual sync with zero subscriptions keeps PENDING
- **WHEN** an operator clicks "Sincronizar desde Stripe" on an artist whose `ArtistSubscription.status == PENDING` and whose Stripe customer exists but holds no subscriptions (`ListObject` with `data == []` or plain `[]`)
- **THEN** the system SHALL NOT change `status` (it SHALL remain `PENDING`), SHALL update `customer_email` (from `sget(customer,"email")` if present) and `last_synced_at`, SHALL re-derive `Artist.is_active` via `compute_is_active` (which returns `False` for `PENDING`), and SHALL show the admin success message with the unchanged status (`Pendiente de pago → Pendiente de pago`).

#### Scenario: Manual sync with zero subscriptions flips non-PENDING to CANCELED
- **WHEN** an operator clicks "Sincronizar desde Stripe" on an artist whose `ArtistSubscription.status != PENDING` (e.g., `ACTIVE`, `PAST_DUE`, `CANCELING`) and whose Stripe customer holds no subscriptions (`ListObject` with `data == []`)
- **THEN** the system SHALL set local `status="canceled"`, persist `Artist.is_active=False` via `compute_is_active`, and update `last_synced_at` / `customer_email`.

#### Scenario: Manual sync handles ListObject correctly
- **WHEN** `Subscription.list` returns a `ListObject` (real SDK, `stripe/_list_object.py:99`) rather than a plain list
- **THEN** the system SHALL NOT raise `KeyError` on integer indexing and SHALL read the subscription from `ListObject.data[0]` (or its empty check via `not ListObject.data`), so operators never see the crash at `/admin/artworks/artist/<id>/sync-from-stripe/`.

#### Scenario: Manual sync handles StripeObject without dict.get

- **WHEN** `ListObject.data[0]` is a `StripeObject` (`stripe/_stripe_object.py:163` blocks `dict.get` in v15)
- **THEN** the system SHALL NOT raise `AttributeError: 'get' is a dict method` and SHALL read fields via `sget` (`obj[key]` then `getattr`) and store `raw_state` via `to_plain_dict`, so sync succeeds for both plain `dict` mocks and real `StripeObject`.

#### Scenario: Manual sync handles Decimal payloads

- **WHEN** the Stripe subscription/invoice payload contains `Decimal` (e.g., `unit_amount_decimal: Decimal("9.99")` in v15)
- **THEN** the system SHALL NOT raise `TypeError: Object of type Decimal is not JSON serializable` at `json/encoder.py:180` and SHALL persist `raw_state` as JSON-serializable plain `dict` via `to_plain_dict(for_json=True)` / `_convert_decimals` (`Decimal→str`).

