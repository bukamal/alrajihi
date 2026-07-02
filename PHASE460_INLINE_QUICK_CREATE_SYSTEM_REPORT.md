# Phase460 — Unified Inline Quick Create System

## Scope
Implemented a project-wide inline quick-create foundation without deleting any feature or file and without changing database schema.

## Implemented

1. Added a non-Qt central registry:
   - `alrajhi_client/ui/inline_quick_create_registry.py`
   - Entities covered: `category`, `unit`, `customer`, `supplier`, `item`
   - Defines mode, fields, permission policy, duplicate behavior, and official service/gateway boundary.

2. Added the reusable inline widget:
   - `alrajhi_client/ui/inline_quick_create.py`
   - `InlineQuickCreatePanel(QFrame)`
   - Inline-first behavior: no `QDialog`, no `exec()`, no new workspace tab.
   - Emits `created(entity_type, result)` and lets the host refresh/select records.
   - Saves through existing services:
     - categories/items via `product_service`
     - customers/suppliers via `entity_service`
   - Keeps local/server/client behavior aligned with existing gateway/service boundaries.

3. Material editor integration:
   - `alrajhi_client/features/items/item_editor_tab.py`
   - Replaced the category quick-create dialog with inline category panel.
   - After save: reloads categories and selects the new/existing category automatically.

4. Legacy material dialog integration:
   - `alrajhi_client/views/dialogs/item_dialog.py`
   - Replaced the category quick-create dialog with the same inline panel.
   - Preserves old dialog itself as a legacy material form, but its quick creation is now inline and unified.

5. Transaction document integration:
   - `alrajhi_client/features/transactions/transaction_document_tab.py`
   - Added inline quick-create button/panel for customer in sales documents.
   - Added inline quick-create button/panel for supplier in purchase documents.
   - Added inline quick-create button/panel for item/material in sales/purchase documents.
   - After creating a customer/supplier: reloads parties and selects the new/existing party.
   - After creating an item: refreshes material lookup and tries to add it to the invoice line grid.
   - Disabled item quick-create in return documents to avoid unsafe return-entry behavior.

6. Added translations for Arabic, German, English, and French:
   - quick-create titles
   - tooltips
   - validation/error/success messages
   - customer/supplier/unit field labels

7. Added/updated tests:
   - `tests/test_phase460_inline_quick_create_system.py`
   - Updated `tests/test_phase459_material_creation_ux.py` to reflect inline-first behavior.

## Validation

Executed successfully:

```text
compileall alrajhi_client tests: OK
Phase459 + Phase460 quick-create tests: 9 passed
Material/document/visual subset: 28 passed
Phase425–457 + Phase459 + Phase460 subset: 154 passed
Transaction/inline workspace subset: 31 passed
i18n/golden runtime subset: 16 passed
```

## Notes

- This phase intentionally does not remove Cafe, Apparel, Restaurant tables, POS, or any other feature.
- The implementation is inline-first but keeps a registry entry for future drawer-style expansion for heavier entities.
- Full interactive GUI testing is still recommended in Windows/X11 because the current execution environment does not provide PyQt runtime.
