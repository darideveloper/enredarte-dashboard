## MODIFIED Requirements

### Requirement: Public artwork status endpoint
The system SHALL expose `GET /api/artworks/artworks/{slug}/status/` as a public endpoint (no authentication) that returns the live sale status and prices of a single artwork. When the artwork is `reserved` with stale `pending_payment` order(s) (`session_expires_at` in the past), the endpoint SHALL reconcile each stale order newest-first against Stripe (via `retrieve_checkout_session`, Stripe fetch outside the row lock, re-verify + mutate inside `select_for_update`, stopping at the first paid-transition) before responding: a hold whose session reports `status == "expired"` with `payment_status != "paid"` SHALL be persisted (`cancel_order`: order → `cancelled`, artwork → `available`) and returned as `available`; a hold reporting `payment_status == "paid"` SHALL be persisted (paid-transition: order → `paid_pending_data`, artwork → `sold`, including the double-sale refund backstop) and returned as `sold`; a hold whose session is still `open` + unpaid, or that is unverifiable (Stripe error/unknown shape, or `session_expires_at=None`), SHALL be returned as stored (`reserved`) with no state change. The hot path (available/sold/live-reserved) SHALL make no Stripe calls and no database writes.

#### Scenario: Available artwork returns live status and prices
- **WHEN** an anonymous `GET` hits `/api/artworks/artworks/{slug}/status/` for an active artwork with an active artist
- **THEN** the response SHALL be `200 OK` with body `{"slug": "<slug>", "status": "<enum>", "status_display": "<Spanish label>", "price_mxn": "<decimal string>", "price_usd": "<decimal string>", "updated_at": "<ISO-8601>"}` and no database write SHALL occur.

#### Scenario: Sold artwork reports sold
- **WHEN** an anonymous `GET` hits the status endpoint for an artwork with `status=sold`
- **THEN** the response SHALL be `200 OK` with `"status": "sold"` and `"status_display": "Vendida"`.

#### Scenario: Reserved artwork reports reserved
- **WHEN** an anonymous `GET` hits the status endpoint for an artwork with `status=reserved`
- **THEN** the response SHALL be `200 OK` with `"status": "reserved"`.

#### Scenario: Stale hold verified expired is freed and reported available
- **WHEN** an anonymous `GET` hits the status endpoint for a `reserved` artwork with stale `pending_payment` order(s) and Stripe reports the newest stale session with `status == "expired"` and `payment_status != "paid"`
- **THEN** the response SHALL be `200 OK` with `"status": "available"`, the order SHALL be persisted as `cancelled` with `cancelled_at` set, the artwork SHALL be persisted as `available`, and the response body (including `updated_at`) SHALL be built from the re-read post-transition row, never the pre-reconcile instance.

#### Scenario: Stale hold verified paid is completed and reported sold
- **WHEN** an anonymous `GET` hits the status endpoint for a `reserved` artwork whose stale `pending_payment` order reports `payment_status == "paid"` at Stripe
- **THEN** the response SHALL be `200 OK` with `"status": "sold"`, the order SHALL be persisted as `paid_pending_data`, the artwork SHALL be persisted as `sold`, and the response body (including `updated_at`) SHALL be built from the re-read post-transition row.

#### Scenario: Stale-local-expiry but Stripe session still open keeps stored state
- **WHEN** an anonymous `GET` hits the status endpoint for a `reserved` artwork with a past `session_expires_at` but Stripe reports the session still `open` and unpaid
- **THEN** the response SHALL be `200 OK` with `"status": "reserved"` and no database write SHALL occur.

#### Scenario: Stale hold unverifiable keeps stored state
- **WHEN** an anonymous `GET` hits the status endpoint for a `reserved` artwork with a past `session_expires_at` but Stripe is unreachable, returns an unknown shape, or the order has `session_expires_at=None`
- **THEN** the response SHALL be `200 OK` with `"status": "reserved"` and no database write SHALL occur.

#### Scenario: Unknown slug returns 404
- **WHEN** a `GET` hits the status endpoint with a slug matching no artwork
- **THEN** the response SHALL be `404 Not Found` with body `{"status": "error", "message": "Not found.", "data": {}}`.

#### Scenario: Inactive artwork returns 404
- **WHEN** a `GET` hits the status endpoint for an artwork with `is_active=False` (or whose artist has `is_active=False`)
- **THEN** the response SHALL be `404 Not Found` with the same error body and no data SHALL be disclosed.

#### Scenario: Response is not cached
- **WHEN** the status endpoint returns `200 OK`
- **THEN** the response SHALL include a `Cache-Control: no-store` header.
