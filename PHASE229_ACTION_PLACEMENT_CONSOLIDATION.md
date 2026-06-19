# Phase 229 — Action Placement Consolidation

## Scope

This phase standardizes document command placement after the Phase 228 UI simplification.

The enforced rule is:

- Document headers are informational only: title, subtitle, document context.
- Local document commands live in the bottom action bar.
- Workspace-level shortcuts remain available through `UnifiedActionBar` and keyboard shortcuts.
- HTML printing remains centralized through `printing_service.render_html()`.

## Updated document shells

The following documents no longer place save/print/export/close actions in the header/title row:

- `features/parties/party_editor_tab.py`
- `features/vouchers/voucher_editor_tab.py`
- `features/finance/documents/expense_document_tab.py`
- `features/items/item_editor_tab.py`
- `features/inventory/documents/inventory_transfer_document_tab.py`
- `features/inventory/documents/warehouse_document_tab.py`
- `features/branches/documents/branch_document_tab.py`
- `features/finance/documents/cashbox_document_tab.py`
- `features/finance/documents/bank_account_document_tab.py`
- `features/users/documents/user_document_tab.py`
- `features/manufacturing/bom_document_tab.py`
- `features/manufacturing/production_order_document_tab.py`

## Notable fixes

- `InventoryTransferDocumentTab` now defines `bottom_print_btn`; previous code connected `self.bottom_print_btn` without creating it.
- Material barcode generation was moved from the document header to the material bottom action bar.
- BOM print/save actions were moved from the header to the BOM bottom action bar.
- Warehouse, branch, cashbox, bank account, and user documents now keep save/close actions in the bottom bar.
- Backward-compatible aliases are retained where older code/tests expect `save_btn`, `print_btn`, or `close_btn` attributes.

## Guards

Added:

- `tools/phase229_action_placement_audit.py`
- `tools/phase229_action_placement_guard.py`

Updated:

- `tools/phase221_voucher_document_shell_guard.py`

## Validation

Executed successfully:

- `python tools/phase229_action_placement_guard.py`
- `python tools/phase228_ui_printing_guard.py`
- `python tools/phase227_database_pyinstaller_guard.py`
- `python tools/phase226_printing_runtime_loader_guard.py`
- `python tools/phase224_windows_release_matrix_guard.py`
- `python tools/phase223_finance_list_legacy_cleanup_guard.py`
- `python tools/phase222_expense_document_shell_guard.py`
- `python tools/phase221_voucher_document_shell_guard.py`
- `python tools/phase220_party_document_shell_guard.py`
- `python tools/phase219_projectwide_architecture_audit.py`
- `python tools/reports_contract_check.py`
- `python tools/advanced_runtime_test.py`
- `python -m compileall -q alrajhi_client alrajhi_server`
