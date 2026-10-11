## Why

The financial ledger (`/admin/finance/financialentry/`) tracks all monetary transactions across the platform—artwork sales, artist commissions, and artist subscriptions (cash and Stripe). Operators currently have no way to extract this ledger data to Excel for accounting, audits, or offline analysis directly from the Django Unfold admin. 

## What Changes

- Add `openpyxl>=3.1,<3.2` dependency to `requirements.txt` to enable styled `.xlsx` workbook generation.
- Implement reusable core export logic in `utils/excel_export.py` following `docs/django-excel-export.md`:
  - Concrete field serialization (dates, naive datetimes, floats with Decimal numeric format, booleans, JSON, files).
  - Foreign key handling decomposing forward relationships into `{field}__str__` and `{field}_id` columns.
  - Forward-related model inspection (`get_related_targets`) for multi-sheet exports.
  - Workbook styling: branded/blue header fill, bold text, frozen top row (`A2`), alternating row striping, number formatting (`#,##0.00`), and auto-sized columns.
- Implement response helper `_excel_response` in `project/admin_base.py`.
- Register two changelist bulk actions on `FinancialEntryAdmin` (integrated into Unfold's bulk actions dropdown):
  - **"Export to Excel"**: Exports selected ledger entries to a single Excel sheet.
  - **"Export to Excel (with related)"**: Exports selected ledger entries on the main sheet and generates dedicated sheets for each referenced forward target (`Artist`, `ArtworkOrder`, `ArtistSubscription`) containing only the referenced records.
- Optimize query performance with `select_related` on forward FKs to avoid N+1 queries during export.
- Explicitly omit global/full app export (`export_all` action, header buttons, and solo templates).

## Capabilities

### New Capabilities
<!-- None -->

### Modified Capabilities
- `finance-admin`: Add requirements and scenarios for exporting selected financial entries from the Unfold changelist actions dropdown to Excel (single-sheet current data and multi-sheet with referenced related data).

## Impact

- **Dependencies**: `openpyxl>=3.1,<3.2` added to `requirements.txt`.
- **Admin**: `FinancialEntryAdmin` (`finance/admin.py`) and admin base (`project/admin_base.py`) gain bulk export action handlers and permissions.
- **Utils**: New utility module `utils/excel_export.py`.
- **Performance**: Safe streaming iteration (`iterator()`) with `select_related` eliminates N+1 queries on FK string representations.
- **Tests**: Comprehensive unit tests covering serialization, FK splitting, sheet generation, multi-sheet related data isolation, and admin action HTTP responses.
