# Phase 219 — Project-wide Architecture / UX Audit

## Summary

- inventory: 10
- low: 1
- medium: 80

## Critical interpretation

The project has largely moved to tab-based documents, but several screens are technically tabs while still being form-stack UI rather than the professional document shell used for transactions.
PartyEditorTab was refactored in Phase 220, VoucherEditorTab in Phase 221, and ExpenseDocumentTab in Phase 222 into its own expense-specific finance document shell.

## Findings

### [medium] Dialog exec() call
- File: `alrajhi_client/action_handler.py:123`
- Area: `dialog-exec`
- Detail: Modal dialog execution detected outside low-level dialog modules.
- Recommendation: Prefer MainWindow open_* document methods for business workflows; keep exec() only for small pickers/confirmations.

### [medium] Dialog exec() call
- File: `alrajhi_client/main.py:39`
- Area: `dialog-exec`
- Detail: Modal dialog execution detected outside low-level dialog modules.
- Recommendation: Prefer MainWindow open_* document methods for business workflows; keep exec() only for small pickers/confirmations.

### [medium] Dialog exec() call
- File: `alrajhi_client/main.py:213`
- Area: `dialog-exec`
- Detail: Modal dialog execution detected outside low-level dialog modules.
- Recommendation: Prefer MainWindow open_* document methods for business workflows; keep exec() only for small pickers/confirmations.

### [medium] Dialog exec() call
- File: `alrajhi_client/main.py:323`
- Area: `dialog-exec`
- Detail: Modal dialog execution detected outside low-level dialog modules.
- Recommendation: Prefer MainWindow open_* document methods for business workflows; keep exec() only for small pickers/confirmations.

### [medium] Dialog exec() call
- File: `alrajhi_client/main.py:336`
- Area: `dialog-exec`
- Detail: Modal dialog execution detected outside low-level dialog modules.
- Recommendation: Prefer MainWindow open_* document methods for business workflows; keep exec() only for small pickers/confirmations.

### [medium] Dialog exec() call
- File: `alrajhi_client/main.py:343`
- Area: `dialog-exec`
- Detail: Modal dialog execution detected outside low-level dialog modules.
- Recommendation: Prefer MainWindow open_* document methods for business workflows; keep exec() only for small pickers/confirmations.

### [medium] Dialog exec() call
- File: `alrajhi_client/main.py:361`
- Area: `dialog-exec`
- Detail: Modal dialog execution detected outside low-level dialog modules.
- Recommendation: Prefer MainWindow open_* document methods for business workflows; keep exec() only for small pickers/confirmations.

### [medium] Legacy dialog reference: ItemDialog
- File: `alrajhi_client/database/connection.py:1269`
- Area: `legacy-dialog`
- Detail: Large modal dialog is still present or referenced. Some references may be explicit fallback paths.
- Recommendation: Primary workflows should open DocumentTab/MainWindow open_* methods. Keep only explicit Legacy*/fallback or small utility dialogs.

### [medium] Dialog exec() call
- File: `alrajhi_client/ui/editable_smart_grid.py:166`
- Area: `dialog-exec`
- Detail: Modal dialog execution detected outside low-level dialog modules.
- Recommendation: Prefer MainWindow open_* document methods for business workflows; keep exec() only for small pickers/confirmations.

### [medium] Dialog exec() call
- File: `alrajhi_client/ui/editable_smart_grid.py:275`
- Area: `dialog-exec`
- Detail: Modal dialog execution detected outside low-level dialog modules.
- Recommendation: Prefer MainWindow open_* document methods for business workflows; keep exec() only for small pickers/confirmations.

### [medium] QDialog class: ColumnChooserDialog
- File: `alrajhi_client/ui/smart_table_view.py:70`
- Area: `qdialog-class`
- Detail: Class inherits QDialog. This may be acceptable for small utility dialogs, but CRUD/document screens should be tabs.
- Recommendation: If this is CRUD/document/edit workflow, migrate to BaseDocumentTab; otherwise document it as allowed utility dialog.

### [medium] QDialog class: FilterBuilderDialog
- File: `alrajhi_client/ui/smart_table_view.py:137`
- Area: `qdialog-class`
- Detail: Class inherits QDialog. This may be acceptable for small utility dialogs, but CRUD/document screens should be tabs.
- Recommendation: If this is CRUD/document/edit workflow, migrate to BaseDocumentTab; otherwise document it as allowed utility dialog.

### [medium] Dialog exec() call
- File: `alrajhi_client/ui/smart_table_view.py:420`
- Area: `dialog-exec`
- Detail: Modal dialog execution detected outside low-level dialog modules.
- Recommendation: Prefer MainWindow open_* document methods for business workflows; keep exec() only for small pickers/confirmations.

### [medium] Dialog exec() call
- File: `alrajhi_client/ui/smart_table_view.py:425`
- Area: `dialog-exec`
- Detail: Modal dialog execution detected outside low-level dialog modules.
- Recommendation: Prefer MainWindow open_* document methods for business workflows; keep exec() only for small pickers/confirmations.

### [medium] Dialog exec() call
- File: `alrajhi_client/ui/smart_table_view.py:536`
- Area: `dialog-exec`
- Detail: Modal dialog execution detected outside low-level dialog modules.
- Recommendation: Prefer MainWindow open_* document methods for business workflows; keep exec() only for small pickers/confirmations.

### [medium] Dialog exec() call
- File: `alrajhi_client/views/custom_table_view.py:141`
- Area: `dialog-exec`
- Detail: Modal dialog execution detected outside low-level dialog modules.
- Recommendation: Prefer MainWindow open_* document methods for business workflows; keep exec() only for small pickers/confirmations.

### [medium] QDialog class: FramelessDialog
- File: `alrajhi_client/views/frameless_dialog.py:8`
- Area: `qdialog-class`
- Detail: Class inherits QDialog. This may be acceptable for small utility dialogs, but CRUD/document screens should be tabs.
- Recommendation: If this is CRUD/document/edit workflow, migrate to BaseDocumentTab; otherwise document it as allowed utility dialog.

### [medium] Dialog exec() call
- File: `alrajhi_client/views/frameless_dialog.py:140`
- Area: `dialog-exec`
- Detail: Modal dialog execution detected outside low-level dialog modules.
- Recommendation: Prefer MainWindow open_* document methods for business workflows; keep exec() only for small pickers/confirmations.

### [medium] Dialog exec() call
- File: `alrajhi_client/views/main_window.py:1104`
- Area: `dialog-exec`
- Detail: Modal dialog execution detected outside low-level dialog modules.
- Recommendation: Prefer MainWindow open_* document methods for business workflows; keep exec() only for small pickers/confirmations.

### [medium] Dialog exec() call
- File: `alrajhi_client/views/main_window.py:1289`
- Area: `dialog-exec`
- Detail: Modal dialog execution detected outside low-level dialog modules.
- Recommendation: Prefer MainWindow open_* document methods for business workflows; keep exec() only for small pickers/confirmations.

### [medium] Dialog exec() call
- File: `alrajhi_client/views/main_window.py:1303`
- Area: `dialog-exec`
- Detail: Modal dialog execution detected outside low-level dialog modules.
- Recommendation: Prefer MainWindow open_* document methods for business workflows; keep exec() only for small pickers/confirmations.

### [medium] Legacy dialog reference: AddEntityDialog
- File: `alrajhi_client/views/dialogs/invoice_dialog.py:1383`
- Area: `legacy-dialog`
- Detail: Large modal dialog is still present or referenced. Some references may be explicit fallback paths.
- Recommendation: Primary workflows should open DocumentTab/MainWindow open_* methods. Keep only explicit Legacy*/fallback or small utility dialogs.

### [medium] Legacy dialog reference: ItemDialog
- File: `alrajhi_client/views/dialogs/invoice_dialog.py:1575`
- Area: `legacy-dialog`
- Detail: Large modal dialog is still present or referenced. Some references may be explicit fallback paths.
- Recommendation: Primary workflows should open DocumentTab/MainWindow open_* methods. Keep only explicit Legacy*/fallback or small utility dialogs.

### [medium] QDialog class: RestaurantLineDialog
- File: `alrajhi_client/views/restaurant/restaurant_pos_widget.py:50`
- Area: `qdialog-class`
- Detail: Class inherits QDialog. This may be acceptable for small utility dialogs, but CRUD/document screens should be tabs.
- Recommendation: If this is CRUD/document/edit workflow, migrate to BaseDocumentTab; otherwise document it as allowed utility dialog.

### [medium] QDialog class: RestaurantAdjustmentsDialog
- File: `alrajhi_client/views/restaurant/restaurant_pos_widget.py:91`
- Area: `qdialog-class`
- Detail: Class inherits QDialog. This may be acceptable for small utility dialogs, but CRUD/document screens should be tabs.
- Recommendation: If this is CRUD/document/edit workflow, migrate to BaseDocumentTab; otherwise document it as allowed utility dialog.

### [medium] QDialog class: RestaurantPaymentDialog
- File: `alrajhi_client/views/restaurant/restaurant_pos_widget.py:133`
- Area: `qdialog-class`
- Detail: Class inherits QDialog. This may be acceptable for small utility dialogs, but CRUD/document screens should be tabs.
- Recommendation: If this is CRUD/document/edit workflow, migrate to BaseDocumentTab; otherwise document it as allowed utility dialog.

### [medium] Dialog exec() call
- File: `alrajhi_client/views/restaurant/restaurant_pos_widget.py:464`
- Area: `dialog-exec`
- Detail: Modal dialog execution detected outside low-level dialog modules.
- Recommendation: Prefer MainWindow open_* document methods for business workflows; keep exec() only for small pickers/confirmations.

### [medium] Dialog exec() call
- File: `alrajhi_client/views/restaurant/restaurant_pos_widget.py:533`
- Area: `dialog-exec`
- Detail: Modal dialog execution detected outside low-level dialog modules.
- Recommendation: Prefer MainWindow open_* document methods for business workflows; keep exec() only for small pickers/confirmations.

### [medium] Dialog exec() call
- File: `alrajhi_client/views/restaurant/restaurant_pos_widget.py:549`
- Area: `dialog-exec`
- Detail: Modal dialog execution detected outside low-level dialog modules.
- Recommendation: Prefer MainWindow open_* document methods for business workflows; keep exec() only for small pickers/confirmations.

### [medium] Dialog exec() call
- File: `alrajhi_client/views/widgets/audit_log_widget.py:198`
- Area: `dialog-exec`
- Detail: Modal dialog execution detected outside low-level dialog modules.
- Recommendation: Prefer MainWindow open_* document methods for business workflows; keep exec() only for small pickers/confirmations.

### [medium] QDialog class: BranchDialog
- File: `alrajhi_client/views/widgets/branches_widget.py:18`
- Area: `qdialog-class`
- Detail: Class inherits QDialog. This may be acceptable for small utility dialogs, but CRUD/document screens should be tabs.
- Recommendation: If this is CRUD/document/edit workflow, migrate to BaseDocumentTab; otherwise document it as allowed utility dialog.

### [medium] Dialog exec() call
- File: `alrajhi_client/views/widgets/branches_widget.py:191`
- Area: `dialog-exec`
- Detail: Modal dialog execution detected outside low-level dialog modules.
- Recommendation: Prefer MainWindow open_* document methods for business workflows; keep exec() only for small pickers/confirmations.

### [medium] Dialog exec() call
- File: `alrajhi_client/views/widgets/branches_widget.py:217`
- Area: `dialog-exec`
- Detail: Modal dialog execution detected outside low-level dialog modules.
- Recommendation: Prefer MainWindow open_* document methods for business workflows; keep exec() only for small pickers/confirmations.

### [medium] Dialog exec() call
- File: `alrajhi_client/views/widgets/categories_widget.py:199`
- Area: `dialog-exec`
- Detail: Modal dialog execution detected outside low-level dialog modules.
- Recommendation: Prefer MainWindow open_* document methods for business workflows; keep exec() only for small pickers/confirmations.

### [medium] Dialog exec() call
- File: `alrajhi_client/views/widgets/categories_widget.py:286`
- Area: `dialog-exec`
- Detail: Modal dialog execution detected outside low-level dialog modules.
- Recommendation: Prefer MainWindow open_* document methods for business workflows; keep exec() only for small pickers/confirmations.

### [medium] Legacy dialog reference: InvoiceDialog
- File: `alrajhi_client/views/widgets/invoices_widget.py:13`
- Area: `legacy-dialog`
- Detail: Large modal dialog is still present or referenced. Some references may be explicit fallback paths.
- Recommendation: Primary workflows should open DocumentTab/MainWindow open_* methods. Keep only explicit Legacy*/fallback or small utility dialogs.

### [medium] Dialog exec() call
- File: `alrajhi_client/views/widgets/items_widget.py:336`
- Area: `dialog-exec`
- Detail: Modal dialog execution detected outside low-level dialog modules.
- Recommendation: Prefer MainWindow open_* document methods for business workflows; keep exec() only for small pickers/confirmations.

### [medium] Dialog exec() call
- File: `alrajhi_client/views/widgets/items_widget.py:343`
- Area: `dialog-exec`
- Detail: Modal dialog execution detected outside low-level dialog modules.
- Recommendation: Prefer MainWindow open_* document methods for business workflows; keep exec() only for small pickers/confirmations.

### [medium] Legacy dialog reference: ProductionDetailsDialog
- File: `alrajhi_client/views/widgets/manufacturing_widget.py:478`
- Area: `legacy-dialog`
- Detail: Large modal dialog is still present or referenced. Some references may be explicit fallback paths.
- Recommendation: Primary workflows should open DocumentTab/MainWindow open_* methods. Keep only explicit Legacy*/fallback or small utility dialogs.

### [medium] Legacy dialog reference: BOMDialog
- File: `alrajhi_client/views/widgets/manufacturing_widget.py:404`
- Area: `legacy-dialog`
- Detail: Large modal dialog is still present or referenced. Some references may be explicit fallback paths.
- Recommendation: Primary workflows should open DocumentTab/MainWindow open_* methods. Keep only explicit Legacy*/fallback or small utility dialogs.

### [medium] Legacy dialog reference: ProductionOrderDialog
- File: `alrajhi_client/views/widgets/manufacturing_widget.py:456`
- Area: `legacy-dialog`
- Detail: Large modal dialog is still present or referenced. Some references may be explicit fallback paths.
- Recommendation: Primary workflows should open DocumentTab/MainWindow open_* methods. Keep only explicit Legacy*/fallback or small utility dialogs.

### [medium] Dialog exec() call
- File: `alrajhi_client/views/widgets/manufacturing_widget.py:363`
- Area: `dialog-exec`
- Detail: Modal dialog execution detected outside low-level dialog modules.
- Recommendation: Prefer MainWindow open_* document methods for business workflows; keep exec() only for small pickers/confirmations.

### [medium] Dialog exec() call
- File: `alrajhi_client/views/widgets/manufacturing_widget.py:383`
- Area: `dialog-exec`
- Detail: Modal dialog execution detected outside low-level dialog modules.
- Recommendation: Prefer MainWindow open_* document methods for business workflows; keep exec() only for small pickers/confirmations.

### [medium] Dialog exec() call
- File: `alrajhi_client/views/widgets/manufacturing_widget.py:406`
- Area: `dialog-exec`
- Detail: Modal dialog execution detected outside low-level dialog modules.
- Recommendation: Prefer MainWindow open_* document methods for business workflows; keep exec() only for small pickers/confirmations.

### [medium] Dialog exec() call
- File: `alrajhi_client/views/widgets/manufacturing_widget.py:458`
- Area: `dialog-exec`
- Detail: Modal dialog execution detected outside low-level dialog modules.
- Recommendation: Prefer MainWindow open_* document methods for business workflows; keep exec() only for small pickers/confirmations.

### [medium] Dialog exec() call
- File: `alrajhi_client/views/widgets/manufacturing_widget.py:480`
- Area: `dialog-exec`
- Detail: Modal dialog execution detected outside low-level dialog modules.
- Recommendation: Prefer MainWindow open_* document methods for business workflows; keep exec() only for small pickers/confirmations.

### [medium] Dialog exec() call
- File: `alrajhi_client/views/widgets/pos_widget.py:539`
- Area: `dialog-exec`
- Detail: Modal dialog execution detected outside low-level dialog modules.
- Recommendation: Prefer MainWindow open_* document methods for business workflows; keep exec() only for small pickers/confirmations.

### [medium] Dialog exec() call
- File: `alrajhi_client/views/widgets/returns_widget.py:411`
- Area: `dialog-exec`
- Detail: Modal dialog execution detected outside low-level dialog modules.
- Recommendation: Prefer MainWindow open_* document methods for business workflows; keep exec() only for small pickers/confirmations.

### [medium] Dialog exec() call
- File: `alrajhi_client/views/widgets/returns_widget.py:635`
- Area: `dialog-exec`
- Detail: Modal dialog execution detected outside low-level dialog modules.
- Recommendation: Prefer MainWindow open_* document methods for business workflows; keep exec() only for small pickers/confirmations.

### [medium] Dialog exec() call
- File: `alrajhi_client/views/widgets/returns_widget.py:689`
- Area: `dialog-exec`
- Detail: Modal dialog execution detected outside low-level dialog modules.
- Recommendation: Prefer MainWindow open_* document methods for business workflows; keep exec() only for small pickers/confirmations.

### [medium] Dialog exec() call
- File: `alrajhi_client/views/widgets/returns_widget.py:1035`
- Area: `dialog-exec`
- Detail: Modal dialog execution detected outside low-level dialog modules.
- Recommendation: Prefer MainWindow open_* document methods for business workflows; keep exec() only for small pickers/confirmations.

### [medium] Dialog exec() call
- File: `alrajhi_client/views/widgets/returns_widget.py:1059`
- Area: `dialog-exec`
- Detail: Modal dialog execution detected outside low-level dialog modules.
- Recommendation: Prefer MainWindow open_* document methods for business workflows; keep exec() only for small pickers/confirmations.

### [medium] Dialog exec() call
- File: `alrajhi_client/views/widgets/returns_widget.py:1494`
- Area: `dialog-exec`
- Detail: Modal dialog execution detected outside low-level dialog modules.
- Recommendation: Prefer MainWindow open_* document methods for business workflows; keep exec() only for small pickers/confirmations.

### [medium] Dialog exec() call
- File: `alrajhi_client/views/widgets/returns_widget.py:1518`
- Area: `dialog-exec`
- Detail: Modal dialog execution detected outside low-level dialog modules.
- Recommendation: Prefer MainWindow open_* document methods for business workflows; keep exec() only for small pickers/confirmations.

### [medium] Direct QSettings in UI/feature layer
- File: `alrajhi_client/views/widgets/returns_widget.py:3`
- Area: `settings-boundary`
- Detail: UI/feature layer should use settings_service/preferences wrappers, not QSettings directly.
- Recommendation: Move persistence to settings_service or a scoped preferences helper using user/branch/profile.

### [medium] Dialog exec() call
- File: `alrajhi_client/views/widgets/settings_widget.py:1638`
- Area: `dialog-exec`
- Detail: Modal dialog execution detected outside low-level dialog modules.
- Recommendation: Prefer MainWindow open_* document methods for business workflows; keep exec() only for small pickers/confirmations.

### [medium] Dialog exec() call
- File: `alrajhi_client/views/widgets/settings_widget.py:1782`
- Area: `dialog-exec`
- Detail: Modal dialog execution detected outside low-level dialog modules.
- Recommendation: Prefer MainWindow open_* document methods for business workflows; keep exec() only for small pickers/confirmations.

### [medium] QDialog class: UserDialog
- File: `alrajhi_client/views/widgets/users_widget.py:191`
- Area: `qdialog-class`
- Detail: Class inherits QDialog. This may be acceptable for small utility dialogs, but CRUD/document screens should be tabs.
- Recommendation: If this is CRUD/document/edit workflow, migrate to BaseDocumentTab; otherwise document it as allowed utility dialog.

### [medium] Dialog exec() call
- File: `alrajhi_client/views/widgets/users_widget.py:164`
- Area: `dialog-exec`
- Detail: Modal dialog execution detected outside low-level dialog modules.
- Recommendation: Prefer MainWindow open_* document methods for business workflows; keep exec() only for small pickers/confirmations.

### [medium] Dialog exec() call
- File: `alrajhi_client/views/widgets/users_widget.py:178`
- Area: `dialog-exec`
- Detail: Modal dialog execution detected outside low-level dialog modules.
- Recommendation: Prefer MainWindow open_* document methods for business workflows; keep exec() only for small pickers/confirmations.

### [medium] Dialog exec() call
- File: `alrajhi_client/views/widgets/users_widget.py:308`
- Area: `dialog-exec`
- Detail: Modal dialog execution detected outside low-level dialog modules.
- Recommendation: Prefer MainWindow open_* document methods for business workflows; keep exec() only for small pickers/confirmations.

### [medium] Dialog exec() call
- File: `alrajhi_client/views/widgets/warehouses_widget.py:638`
- Area: `dialog-exec`
- Detail: Modal dialog execution detected outside low-level dialog modules.
- Recommendation: Prefer MainWindow open_* document methods for business workflows; keep exec() only for small pickers/confirmations.

### [medium] Dialog exec() call
- File: `alrajhi_client/views/widgets/warehouses_widget.py:743`
- Area: `dialog-exec`
- Detail: Modal dialog execution detected outside low-level dialog modules.
- Recommendation: Prefer MainWindow open_* document methods for business workflows; keep exec() only for small pickers/confirmations.

### [medium] Direct QSettings in UI/feature layer
- File: `alrajhi_client/views/widgets/components/table_preferences.py:4`
- Area: `settings-boundary`
- Detail: UI/feature layer should use settings_service/preferences wrappers, not QSettings directly.
- Recommendation: Move persistence to settings_service or a scoped preferences helper using user/branch/profile.

### [medium] Dialog exec() call
- File: `alrajhi_client/views/widgets/components/table_toolbar.py:169`
- Area: `dialog-exec`
- Detail: Modal dialog execution detected outside low-level dialog modules.
- Recommendation: Prefer MainWindow open_* document methods for business workflows; keep exec() only for small pickers/confirmations.

### [medium] Legacy dialog reference: InvoiceDialog
- File: `alrajhi_client/features/invoices/invoice_editor_tab.py:4`
- Area: `legacy-dialog`
- Detail: Large modal dialog is still present or referenced. Some references may be explicit fallback paths.
- Recommendation: Primary workflows should open DocumentTab/MainWindow open_* methods. Keep only explicit Legacy*/fallback or small utility dialogs.

### [medium] Legacy dialog reference: ItemDialog
- File: `alrajhi_client/features/items/item_editor_tab.py:48`
- Area: `legacy-dialog`
- Detail: Large modal dialog is still present or referenced. Some references may be explicit fallback paths.
- Recommendation: Primary workflows should open DocumentTab/MainWindow open_* methods. Keep only explicit Legacy*/fallback or small utility dialogs.

### [medium] Dialog exec() call
- File: `alrajhi_client/features/items/item_editor_tab.py:633`
- Area: `dialog-exec`
- Detail: Modal dialog execution detected outside low-level dialog modules.
- Recommendation: Prefer MainWindow open_* document methods for business workflows; keep exec() only for small pickers/confirmations.

### [medium] Legacy dialog reference: BOMDialog
- File: `alrajhi_client/features/manufacturing/bom_document_tab.py:29`
- Area: `legacy-dialog`
- Detail: Large modal dialog is still present or referenced. Some references may be explicit fallback paths.
- Recommendation: Primary workflows should open DocumentTab/MainWindow open_* methods. Keep only explicit Legacy*/fallback or small utility dialogs.

### [medium] Legacy dialog reference: ProductionDetailsDialog
- File: `alrajhi_client/features/manufacturing/production_order_document_tab.py:40`
- Area: `legacy-dialog`
- Detail: Large modal dialog is still present or referenced. Some references may be explicit fallback paths.
- Recommendation: Primary workflows should open DocumentTab/MainWindow open_* methods. Keep only explicit Legacy*/fallback or small utility dialogs.

### [medium] Legacy dialog reference: ProductionOrderDialog
- File: `alrajhi_client/features/manufacturing/production_order_document_tab.py:41`
- Area: `legacy-dialog`
- Detail: Large modal dialog is still present or referenced. Some references may be explicit fallback paths.
- Recommendation: Primary workflows should open DocumentTab/MainWindow open_* methods. Keep only explicit Legacy*/fallback or small utility dialogs.

### [medium] Legacy dialog reference: ProductionDetailsDialog
- File: `alrajhi_client/features/manufacturing/production_order_lifecycle_tab.py:42`
- Area: `legacy-dialog`
- Detail: Large modal dialog is still present or referenced. Some references may be explicit fallback paths.
- Recommendation: Primary workflows should open DocumentTab/MainWindow open_* methods. Keep only explicit Legacy*/fallback or small utility dialogs.

### [medium] Dialog exec() call
- File: `alrajhi_client/features/manufacturing/production_order_lifecycle_tab.py:399`
- Area: `dialog-exec`
- Detail: Modal dialog execution detected outside low-level dialog modules.
- Recommendation: Prefer MainWindow open_* document methods for business workflows; keep exec() only for small pickers/confirmations.

### [medium] Dialog exec() call
- File: `alrajhi_client/features/manufacturing/production_order_lifecycle_tab.py:441`
- Area: `dialog-exec`
- Detail: Modal dialog execution detected outside low-level dialog modules.
- Recommendation: Prefer MainWindow open_* document methods for business workflows; keep exec() only for small pickers/confirmations.

### [medium] Dialog exec() call
- File: `alrajhi_client/features/manufacturing/production_order_lifecycle_tab.py:465`
- Area: `dialog-exec`
- Detail: Modal dialog execution detected outside low-level dialog modules.
- Recommendation: Prefer MainWindow open_* document methods for business workflows; keep exec() only for small pickers/confirmations.

### [medium] Dialog exec() call
- File: `alrajhi_client/features/manufacturing/production_order_lifecycle_tab.py:477`
- Area: `dialog-exec`
- Detail: Modal dialog execution detected outside low-level dialog modules.
- Recommendation: Prefer MainWindow open_* document methods for business workflows; keep exec() only for small pickers/confirmations.

### [medium] Legacy dialog reference: SalesReturnDialog
- File: `alrajhi_client/features/returns/return_editor_tabs.py:11`
- Area: `legacy-dialog`
- Detail: Large modal dialog is still present or referenced. Some references may be explicit fallback paths.
- Recommendation: Primary workflows should open DocumentTab/MainWindow open_* methods. Keep only explicit Legacy*/fallback or small utility dialogs.

### [medium] Legacy dialog reference: PurchaseReturnDialog
- File: `alrajhi_client/features/returns/return_editor_tabs.py:12`
- Area: `legacy-dialog`
- Detail: Large modal dialog is still present or referenced. Some references may be explicit fallback paths.
- Recommendation: Primary workflows should open DocumentTab/MainWindow open_* methods. Keep only explicit Legacy*/fallback or small utility dialogs.

### [medium] Direct QSettings in UI/feature layer
- File: `alrajhi_client/features/pos/pos_preferences.py:7`
- Area: `settings-boundary`
- Detail: UI/feature layer should use settings_service/preferences wrappers, not QSettings directly.
- Recommendation: Move persistence to settings_service or a scoped preferences helper using user/branch/profile.

### [medium] Direct QSettings in UI/feature layer
- File: `alrajhi_client/features/transactions/grids/transaction_grid_preferences.py:12`
- Area: `settings-boundary`
- Detail: UI/feature layer should use settings_service/preferences wrappers, not QSettings directly.
- Recommendation: Move persistence to settings_service or a scoped preferences helper using user/branch/profile.
