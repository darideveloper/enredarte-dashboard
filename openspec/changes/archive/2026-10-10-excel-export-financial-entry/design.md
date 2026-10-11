## Context

See `proposal.md` for motivation. The project currently runs Django 5.2 and `django-unfold==0.77.1`. The financial ledger is managed via `FinancialEntryAdmin` in `finance/admin.py`, which extends `ModelAdminUnfoldBase` in `project/admin_base.py`. `docs/django-excel-export.md` documents an established reusable pattern for Django + Unfold Excel exports using `openpyxl`.

## Goals / Non-Goals

**Goals:**
- Provide changelist bulk actions "Export to Excel" (single sheet) and "Export to Excel (with related)" (multi-sheet) in `FinancialEntryAdmin`.
- Render foreign key fields as `{field}__str__` and `{field}_id` pairs on the main sheet.
- Restrict related sheets to directly referenced models and rows (single-hop, no transitive traversal, no unreferenced rows).
- Apply consistent visual formatting (primary header fill, frozen `A2` row, zebra rows, currency formatting, auto-sized columns).
- Prevent N+1 queries by leveraging `select_related` on foreign key fields.
- Strictly adhere to Django test conventions (`python manage.py test`) and maintain clean test coverage.

**Non-Goals:**
- Global/app-wide export (`export_all`, `build_full_app_workbook`, header buttons, or solo template overrides).
- Reverse foreign key or Many-to-Many export sheets.
- Client-side or JavaScript-based export implementations.

## Decisions

### 1. Reusable Pure Workbook Utility (`utils/excel_export.py`)
- **Decision**: Keep all `openpyxl` workbook generation, styling, and model serialization in a decoupled utility module `utils/excel_export.py`.
- **Rationale**: Keeps admin classes lightweight and facilitates isolated unit testing without requiring full HTTP request cycles.
- **Alternatives considered**: Embedding export logic inside `ModelAdmin` methods—rejected due to tight coupling and poor reusability.

### 2. Dual Foreign Key Columns (`{field}__str__` and `{field}_id`)
- **Decision**: For every concrete forward foreign key/OneToOne field (excluding auto-created), emit two consecutive columns:
  - Header: `f"{field.name}__str__"` → Value: `str(getattr(obj, field.name))` (or empty string if `None`).
  - Header: `field.attname` (e.g. `artist_id`) → Value: `getattr(obj, field.attname)`.
- **Rationale**: Exactly matches user requirements and enables human readability while preserving database keys for reconciliation.
- **Alternatives considered**: Exporting only ID or only string representation—rejected because financial auditing requires both readable labels and exact IDs.

### 3. Action Placement on `ModelAdminUnfoldBase`
- **Decision**: Define the export actions `export_selected` and `export_selected_with_related` on `ModelAdminUnfoldBase` in `project/admin_base.py`.
- **Rationale**: Subclasses like `FinancialEntryAdmin` inherit the actions by default. Any admin can customize or override them without duplicate code.
- **Alternatives considered**: Defining them strictly on `FinancialEntryAdmin`—rejected because placing them in `ModelAdminUnfoldBase` follows the standard architecture in `docs/django-excel-export.md`.

### 4. Referenced Rows Only & Omission of Unreferenced Target Sheets
- **Decision**: When `include_related=True`, collect distinct non-null IDs for each forward foreign key using `queryset.values_list(attname, flat=True)`. If a target model has no referenced IDs among the selected rows (e.g., no selected entry has an `order`), skip creating a sheet for that model.
- **Rationale**: Avoids cluttering the workbook with empty sheets while ensuring all relevant context is present.
- **Alternatives considered**: Emitting an empty sheet with just column headers—rejected because empty tabs provide no value to operators.

### 5. Datetime and Numeric Serialization
- **Decision**:
  - `DateTimeField`: Strip timezone (`value.replace(tzinfo=None)`) before writing to Excel cells, as Excel does not support timezone offsets.
  - `DecimalField`: Convert to `float(value)` for openpyxl cell value and assign `cell.number_format = '#,##0.00'`.
- **Rationale**: Ensures Excel natively interprets numbers as calculable floats with currency-style formatting, and prevents openpyxl timezone exceptions.

### 6. Streaming and N+1 Query Optimization
- **Decision**: Before iterating over the selected queryset, dynamically apply `select_related(*fk_names)` for all forward foreign keys on the model, and stream with `.iterator()`.
- **Rationale**: Resolves `artist`, `order`, and `subscription` in a single SQL query, preventing catastrophic N+1 query overhead on large selections.

## Risks / Trade-offs

- **[Memory usage on large selections]** → Mitigated by using `queryset.iterator()` to stream database records. If querysets exceed 50,000 rows in the future, can be migrated to `StreamingHttpResponse` or background worker.
- **[Decimal precision loss converting to float]** → Negligible for currency amounts (2 decimal places); original database values remain authoritative.
- **[Sheet title collisions or length limits]** → Mitigated by `sanitize_sheet_name`, which truncates names to 31 characters, sanitizes illegal characters, and appends `_2`, `_3` on collisions.
