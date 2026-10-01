## ADDED Requirements

### Requirement: Finanzas admin list is read-only except reconciled

The system SHALL register a `FinancialEntryAdmin` (Unfold) under a "Finanzas" admin section listing model "Movimientos". The changelist SHALL display date, kind, artist, signed amount (color-coded green for positive, red for negative), currency, source reference, and `reconciled`. All fields SHALL be read-only except `reconciled`, which SHALL be editable inline from the changelist via Django's `list_editable`. The admin SHALL forbid adding and deleting ledger entries. Operator-visible labels SHALL be Spanish.

#### Scenario: Inline reconcile from the list
- **WHEN** an operator ticks `reconciled` on a row and saves the changelist
- **THEN** the entry SHALL be updated without opening its detail page and no other field SHALL change.

#### Scenario: Adding and deleting are blocked
- **WHEN** an operator opens the ledger changelist or a detail page
- **THEN** no "add entry" button SHALL be available and deletion SHALL be refused.

#### Scenario: Amounts are signed and color-coded
- **WHEN** a positive `artwork_sale` entry and a negative `artist_commission` entry are listed
- **THEN** the income SHALL render positive (green) and the commission negative (red).

### Requirement: All admin-visible texts are Spanish

The "Finanzas" admin SHALL render every operator-visible text in Spanish, following `docs/django-i18n-es-admin.md`: the app `verbose_name` ("Finanzas"), the sidebar/section title and model name ("Movimientos"), every field `verbose_name`/`help_text`, the display labels of all choices (`kind`, `payment_method`, `currency`), changelist column headers, filter titles, the totals partial labels ("Vista actual", "Total del sistema", "Ingresos", "Comisiones", "Neto", and the entry count), the empty-state text, and any custom admin view copy. Stored values (e.g. `kind="artwork_sale"`, `payment_method="stripe"`) SHALL remain language-neutral English; only their displayed labels SHALL be Spanish. Generic admin chrome SHALL be Spanish via Django's shipped `es` catalog (`LANGUAGE_CODE = "es"`), with no new translation catalog unless an Unfold-only string requires it. The ledger's `payment_method` display label SHALL read "En línea" for `stripe` and "Efectivo" for `cash`, matching the `ArtistSubscription` admin.

#### Scenario: Section, model and field labels are Spanish
- **WHEN** an operator opens the "Finanzas" section and the "Movimientos" changelist
- **THEN** the app name, model name, every column header, and every field label SHALL be Spanish.

#### Scenario: Choice labels are Spanish
- **WHEN** an operator opens a `kind`, `payment_method`, or `currency` filter/dropdown
- **THEN** the displayed labels SHALL be Spanish ("Venta de obra", "Comisión de artista", "Pago de suscripción", "Efectivo", "En línea", "MXN", "USD") while the stored values remain language-neutral.

#### Scenario: Totals partial labels are Spanish
- **WHEN** the totals partial renders
- **THEN** its labels SHALL be Spanish ("Vista actual", "Total del sistema", "Ingresos", "Comisiones", "Neto").

### Requirement: Month drill-down and custom filters

The ledger changelist SHALL support drilling down by month via `date_hierarchy` on `occurred_on`, and SHALL provide filters for date range, artist, kind, payment method, currency, and reconciled state.

#### Scenario: Filter by month
- **WHEN** an operator selects a month in the date drill-down
- **THEN** only entries with `occurred_on` in that month SHALL be listed.

#### Scenario: Filter by kind, artist, payment method, and currency
- **WHEN** an operator filters by `kind=artist_commission`, an artist, `payment_method=cash`, and `currency=MXN`
- **THEN** only entries matching all selected filters SHALL be listed.

#### Scenario: Filter by reconciled state
- **WHEN** an operator filters by `reconciled=True`
- **THEN** only reconciled entries SHALL be listed.

### Requirement: Per-currency totals visible under the filtered list

The ledger changelist SHALL display totals computed over the currently filtered queryset, grouped per currency, showing for each currency the income subtotal (sum of positive amounts), the expense subtotal (sum of negative amounts, i.e. artist commissions), and the signed net total, plus the entry count, without requiring a separate report page.

#### Scenario: Totals reflect the active filters
- **WHEN** the list is filtered (e.g. by artist or month)
- **THEN** the totals SHALL be recomputed for the filtered set only.

#### Scenario: Totals split by currency
- **WHEN** the filtered set contains both MXN and USD entries
- **THEN** a separate income / expense / net breakdown SHALL be shown for MXN and for USD; no combined cross-currency figure SHALL be produced.

#### Scenario: Income, expense, and net are consistent
- **WHEN** the filtered set contains `+1000` and `-300`
- **THEN** the line SHALL show income `+1000`, expenses `-300`, and net `+700` for that currency.

### Requirement: Full-system totals alongside filtered totals

The ledger changelist SHALL display, in the same view, a full-system total in addition to the filtered total. The full-system total SHALL be computed over all ledger entries regardless of any active filter or month drill-down, and SHALL be grouped per currency like the filtered total, with the same income / expense / net breakdown. Both totals SHALL be shown together, clearly labelled to distinguish the current filtered view from the whole system.

#### Scenario: Full total ignores active filters
- **WHEN** the list is filtered by an artist or a month
- **THEN** the "total del sistema" SHALL remain unchanged (all entries, all time), while the "vista actual" total SHALL reflect only the filtered set.

#### Scenario: Both totals visible with no results
- **WHEN** the active filters match no entries
- **THEN** the view SHALL still display the full-system total per currency.

#### Scenario: Both totals split by currency
- **WHEN** the ledger contains MXN and USD entries
- **THEN** both the filtered and the full-system totals SHALL each be shown as income / expense / net per currency, with no combined cross-currency figure.

### Requirement: Totals update with month drill-down

The per-currency totals SHALL also apply when a month is selected via the date drill-down, so an operator can read a single month's income, commissions, and net at a glance.

#### Scenario: Single-month totals
- **WHEN** an operator selects one month in the drill-down
- **THEN** the "vista actual" totals SHALL show that month's income / expense / net per currency, while "total del sistema" SHALL remain all-time.
