## 1. Dependencies and Environment Setup

- [x] 1.1 Add `openpyxl>=3.1,<3.2` to `requirements.txt` and install it into `venv`, verifying with `venv/bin/python -c "import openpyxl; print(openpyxl.__version__)"`.

## 2. Core Excel Export Utilities

- [x] 2.1 Create `utils/excel_export.py` with `sanitize_sheet_name`, `serialize_value`, and `columns_for_model`, verifying that foreign keys are split into `{field}__str__` and `{field}_id` pairs.
- [x] 2.2 Implement workbook styling (`style_sheet` with `#2563EB` header, bold white text, frozen `A2`, zebra striping `#F9FAFB` / `#FFFFFF`, decimal number format `#,##0.00`) and column autosizing (`autosize_columns`) in `utils/excel_export.py`.
- [x] 2.3 Implement forward-related target detection (`get_related_targets`) and workbook generation (`build_workbook_for_queryset`) in `utils/excel_export.py`, supporting single-sheet (`include_related=False`) and multi-sheet (`include_related=True`) exports for referenced rows only.

## 3. Admin Integration

- [x] 3.1 Implement `_excel_response(workbook, filename)` HTTP response helper in `project/admin_base.py` setting RFC 5987 content-disposition and `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` MIME type.
- [x] 3.2 Add `export_selected` and `export_selected_with_related` bulk actions with `permissions=["view"]` to `ModelAdminUnfoldBase` in `project/admin_base.py`.
- [x] 3.3 Ensure `FinancialEntryAdmin` in `finance/admin.py` exposes both export actions in its changelist actions dropdown and utilizes `select_related("artist", "order", "subscription")` during export streaming.

## 4. Testing and Verification

- [x] 4.1 Add unit tests in `finance/tests.py` covering field value serialization, foreign key column generation (`__str__` and `_id`), and single-sheet workbook creation.
- [x] 4.2 Add unit tests in `finance/tests.py` covering multi-sheet export, verifying that related sheets contain only referenced rows and that unreferenced models do not produce empty sheets.
- [x] 4.3 Add admin integration tests in `finance/tests.py` verifying HTTP POST changelist bulk action execution, view permission gating, empty selection warning messages, and verifying absence of global export header buttons.
- [x] 4.4 Run canonical test command `venv/bin/python manage.py test finance.tests --verbosity=2` and verify all tests pass.
