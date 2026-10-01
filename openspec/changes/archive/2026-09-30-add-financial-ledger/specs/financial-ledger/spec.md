## ADDED Requirements

### Requirement: Append-only signed financial ledger

The system SHALL provide a `finance.FinancialEntry` model recording one immutable row per economic money movement, with a signed `amount` field where income is positive and expenses are negative. Each entry SHALL carry: `occurred_on` (indexed `DateField`), `kind` (choices `artwork_sale`, `artist_commission`, `subscription_payment`), `amount` (signed `DecimalField`, 2 decimals), `currency` (choices `MXN`/`USD`), `artist` (nullable FK to `artworks.Artist`, `SET_NULL`), `payment_method` (nullable choices `cash`/`stripe`), `order` (nullable FK to `artworks.ArtworkOrder`, `SET_NULL`, traceability), `subscription` (nullable FK to `subscriptions.ArtistSubscription`, `SET_NULL`), `reference` (blank `CharField`, source-event key for idempotency), `note` (blank `CharField`), and `reconciled` (boolean, default `False`). The model SHALL follow project conventions: Spanish `verbose_name`/`verbose_name_plural`, Spanish `verbose_name` on every field, `help_text` on non-obvious fields, and a content-based `__str__` that includes date, kind, and signed amount.

#### Scenario: Ledger row from an artwork sale
- **WHEN** an artwork sale is recorded in the ledger
- **THEN** a `FinancialEntry` SHALL exist with `kind="artwork_sale"`, a positive `amount`, the sale `currency`, the selling `artist`, `payment_method="stripe"`, and the originating `order` linked.

#### Scenario: Model admin conventions
- **WHEN** `FinancialEntry` is inspected in the Django admin
- **THEN** it SHALL display Spanish `verbose_name`/`verbose_name_plural`, Spanish field labels with help texts, and a content-based `__str__` (not Django's default `"FinancialEntry object (N)"`).

### Requirement: Income positive, commissions negative

The system SHALL record `artwork_sale` and `subscription_payment` entries with a **positive** `amount`, and `artist_commission` entries with a **negative** `amount`, so that summing `amount` yields net revenue for the filtered set.

#### Scenario: Sale and subscription add, commission subtracts
- **WHEN** a sale of 1000 on an artist with 30% commission and a subscription payment of 500 are recorded
- **THEN** the ledger SHALL contain `+1000` (artwork_sale), `-300` (artist_commission), and `+500` (subscription_payment).

#### Scenario: Net total reflects signed sum
- **WHEN** the entries above are summed
- **THEN** the result SHALL be `1200`.

### Requirement: Artwork sale writes income and frozen commission

When an `ArtworkOrder` transitions to the paid state (via `apply_paid_transition`, including the checkout-completed and async-payment paths), the system SHALL create an `artwork_sale` entry for the order's `amount` and `currency`, and — when the artist's commission percentage is greater than 0 — an `artist_commission` entry whose `amount` is `-(order.amount * artist.commission / 100)` and which **freezes** the artist's commission percentage and resulting amount at that moment. The commission entry's `payment_method` and `artist` SHALL be set; `occurred_on` SHALL be the order's `paid_at` date. The paid transition SHALL remain idempotent: re-delivery SHALL NOT create duplicate entries.

#### Scenario: Paid sale creates two entries with frozen split
- **WHEN** an order of `1000` MXN for an artist with `commission=25` transitions to paid
- **THEN** the ledger SHALL contain `+1000` (`artwork_sale`) and `-250` (`artist_commission`), and editing the artist's commission afterwards SHALL NOT change those entries.

#### Scenario: Zero commission creates income only
- **WHEN** a paid order's artist has `commission=0`
- **THEN** the ledger SHALL contain only the positive `artwork_sale` entry and no `artist_commission` entry.

#### Scenario: Idempotent paid transition does not double-book
- **WHEN** the paid transition is applied more than once for the same order (webhook retry / reconcile)
- **THEN** at most one `artwork_sale` and one `artist_commission` entry SHALL exist for that order.

### Requirement: Refund writes reversal entries

When an `ArtworkOrder` becomes `refunded`, the system SHALL create, for each ledger entry already recorded for that order, an opposite entry that nets the pair to zero (a negative `artwork_sale` for a recorded sale; a positive `artist_commission` for a recorded commission). Reversals SHALL be linked to the same `order`, dated on the refund date, and SHALL never delete or mutate the original entries. When the order has no recorded ledger entry — the double-sale backstop charges and refunds a sale that was never booked — the system SHALL create no entry, so the refund never distorts totals.

#### Scenario: Refund reverses a sale
- **WHEN** a paid order of `1000` with a `-250` commission entry is refunded
- **THEN** the ledger SHALL additionally contain `-1000` (`artwork_sale`) and `+250` (`artist_commission`), and the four entries for that order SHALL sum to `0`.

#### Scenario: Refund is idempotent
- **WHEN** the refund handling runs more than once for the same order
- **THEN** at most one reversal entry per original entry SHALL exist for that order.

#### Scenario: Refund without a recorded sale is a no-op
- **WHEN** the double-sale backstop refunds an order that never had a recorded `artwork_sale` entry
- **THEN** no ledger entry SHALL be created for that order (the charge/refund pair nets to zero).

### Requirement: Stripe subscription payment snapshots the invoice amount

When `invoice.payment_succeeded` is processed for a non-cash `ArtistSubscription`, the system SHALL create a `subscription_payment` entry with the invoice's actual paid amount and currency (`amount_paid` / `currency`), `payment_method="stripe"`, and `occurred_on` set to the payment date. The entry's `reference` SHALL be the Stripe invoice id so that event redelivery does not double-book. Cash rows SHALL continue to be ignored by Stripe webhooks.

#### Scenario: Invoice paid records subscription income
- **WHEN** a Stripe invoice for `500` MXN succeeds for a subscription
- **THEN** the ledger SHALL contain a `+500` (`subscription_payment`, `stripe`) entry linked to the subscription.

#### Scenario: Duplicate invoice delivery is ignored
- **WHEN** the same invoice event is delivered twice
- **THEN** only one `subscription_payment` entry SHALL exist for that invoice `reference`.

#### Scenario: Cash rows untouched by Stripe
- **WHEN** a Stripe invoice event resolves to a `payment_method="cash"` subscription
- **THEN** no ledger entry SHALL be created by the Stripe handler.

### Requirement: Cash confirmation snapshots the plan amount

When an operator confirms a cash payment ("Confirmar pago"), the system SHALL create a `subscription_payment` entry using `BillingPlan.amount` and `currency` captured at confirmation time, `payment_method="cash"`, `artist` set, and `occurred_on` set to the confirmation date. Each execution SHALL count as one monthly payment (one entry), and an exact-duplicate `reference` (same artist and resulting period) SHALL be suppressed.

#### Scenario: Cash confirmation records income
- **WHEN** an operator confirms a cash payment while the plan amount is `500` MXN
- **THEN** the ledger SHALL contain a `+500` (`subscription_payment`, `cash`) entry for that artist.

#### Scenario: Plan price change does not alter past entries
- **WHEN** the plan amount is later changed
- **THEN** previously recorded cash entries SHALL retain their original amount.

### Requirement: Reconciled marker

Every entry SHALL expose a `reconciled` boolean defaulting to `False`, settable by operators to mark the movement as validated. For artist commissions the same flag denotes that the commission has been settled to the artist. The ledger SHALL NOT store who or when the flag was changed.

#### Scenario: Default not reconciled
- **WHEN** any entry is created
- **THEN** its `reconciled` value SHALL be `False`.

#### Scenario: Operator validates a movement
- **WHEN** an operator marks an entry as reconciled
- **THEN** `reconciled` SHALL become `True` regardless of `kind` (sale, commission, or subscription payment).

### Requirement: Historical artwork sales backfill

The system SHALL provide a data migration that creates `artwork_sale` and (when applicable) `artist_commission` entries for existing `ArtworkOrder` rows that have a `paid_at` timestamp and a non-refunded/cancelled status, using each artist's current commission percentage. The migration SHALL be idempotent and SHALL NOT create entries for orders with `paid_at` empty. Subscription entries SHALL NOT be backfilled.

#### Scenario: Backfill creates entries for paid orders
- **WHEN** the migration runs with an existing paid order
- **THEN** a corresponding `artwork_sale` entry and, when the artist's commission is greater than 0, an `artist_commission` entry SHALL exist.

#### Scenario: Backfill skips unpaid orders
- **WHEN** the migration runs with a pending or cancelled order (`paid_at` empty)
- **THEN** no ledger entry SHALL be created for it.

### Requirement: Ledger remains internal

The financial ledger SHALL be internal to the Django Admin. No public REST endpoint or serializer SHALL expose `FinancialEntry` data or artist commission amounts.

#### Scenario: No public exposure
- **WHEN** any public API endpoint is queried
- **THEN** no ledger entry or commission amount SHALL appear in any response payload.
