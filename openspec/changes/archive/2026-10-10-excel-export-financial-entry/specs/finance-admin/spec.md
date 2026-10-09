## ADDED Requirements

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
