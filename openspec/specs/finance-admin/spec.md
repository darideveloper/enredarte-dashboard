# finance-admin Specification

## Purpose
The "Finanzas" Django Admin section: a read-only "Movimientos" ledger changelist with inline reconcile, fully Spanish operator-facing text, month drill-down and filters, and per-currency filtered and full-system totals.
## Requirements
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

### Requirement: Export selected financial entries to Excel

The system SHALL provide an "Exportar a Excel" action in the Unfold admin changelist bulk actions dropdown on `/admin/finance/financialentry/`. When an operator selects one or more financial entries and executes this action, the system SHALL generate and return an `.xlsx` workbook containing a single worksheet titled with the model's plural display name ("Movimientos").

All concrete fields of `FinancialEntry` SHALL be included in the sheet. Normal fields SHALL be serialized into Excel-compatible native values (dates native, datetimes timezone-naive, numbers formatted with two decimal places, booleans, and strings). Every forward foreign key (`artist`, `order`, `subscription`) SHALL be decomposed into two distinct columns:
1. `{field}__str__`: string representation of the related object (empty if null).
2. `{field}_id`: primary key identifier of the related object (empty if null).

The worksheet SHALL be styled with a primary color header row (`#2563EB` fill, bold white text, bottom border), frozen panes below the header (`A2`), alternating row striping (`#F9FAFB` and `#FFFFFF`), and column widths auto-sized to content clamped between 10 and 50 characters.

The action SHALL require view permission on `FinancialEntry`. If the action is triggered with an empty selection, the system SHALL display a warning message ("Selecciona al menos una fila para exportar.") and not generate a workbook.

#### Scenario: Operator exports selected entries to a single sheet
- **WHEN** an operator selects financial entries on the changelist and triggers "Exportar a Excel"
- **THEN** the system SHALL return an `.xlsx` file attachment with a single sheet containing only the selected records, with header row frozen at A2 and styled.

#### Scenario: Foreign key columns render as string and ID pair
- **WHEN** financial entries with foreign keys to artists, orders, or subscriptions are exported
- **THEN** the worksheet SHALL contain `{field}__str__` and `{field}_id` columns for each foreign key field, correctly displaying the related object's label and primary key.

#### Scenario: Export requires view permission
- **WHEN** a user without view permission on `FinancialEntry` attempts to perform the export action
- **THEN** the export action SHALL NOT be accessible or executed.

#### Scenario: Empty selection displays warning message
- **WHEN** an export action is submitted without any selected entries
- **THEN** the system SHALL display a warning message to select at least one row and no file download SHALL occur.

### Requirement: Export selected financial entries to Excel with related data

The system SHALL provide an "Exportar a Excel (con relacionados)" action in the Unfold admin changelist bulk actions dropdown on `/admin/finance/financialentry/`. When an operator selects one or more financial entries and executes this action, the system SHALL generate and return an `.xlsx` workbook containing:
1. A primary sheet with the selected financial entries, formatted identically to the single-sheet export (including `{field}__str__` and `{field}_id` columns).
2. Additional sheets for each forward-related target model (`Artist`, `ArtworkOrder`, `ArtistSubscription`) that is referenced by at least one selected financial entry.

Each related sheet SHALL contain only the rows from the respective target model that are directly referenced by the selected financial entries (single-hop forward foreign keys, referenced rows only). Target models that have zero references among the selected entries SHALL NOT generate an empty sheet. Each related sheet SHALL apply the same visual styling (primary color header, frozen panes at A2, banded rows, auto-sized columns).

#### Scenario: Multi-sheet workbook contains referenced related records
- **WHEN** an operator selects financial entries referencing specific artists, orders, and subscriptions, and executes "Exportar a Excel (con relacionados)"
- **THEN** the system SHALL return an `.xlsx` file containing the primary "Movimientos" sheet plus separate sheets for each referenced model populated only with the referenced records.

#### Scenario: Unreferenced related models do not generate empty sheets
- **WHEN** the selected financial entries have no associated orders (e.g., all entries are cash subscription payments)
- **THEN** the resulting workbook SHALL NOT include an `ArtworkOrder` sheet.

#### Scenario: Related sheets use standardized header and table styling
- **WHEN** related sheets are created in the multi-sheet export
- **THEN** each related sheet SHALL have its top row frozen at A2, header formatted in bold white text on primary fill, and alternating row striping.

### Requirement: No global full app export button

The system SHALL NOT render a global or app-wide export button in the changelist header tools, changeform object tools, or navigation bar. Export functionality SHALL be strictly confined to changelist row selection bulk actions for selected entries.

#### Scenario: Changelist header tools omit global export
- **WHEN** an operator navigates to the financial entry changelist or detail view
- **THEN** no "Export all app data" or global export button SHALL appear in the header action tools.
