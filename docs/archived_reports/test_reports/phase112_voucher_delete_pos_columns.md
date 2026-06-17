# Phase112 – Voucher Delete Button + POS Column Visibility

## Scope
- Add a visible delete action for vouchers in the vouchers screen.
- Preserve the existing voucher reversal accounting path through `voucher_service.delete()`.
- Add user-controlled, persistent column visibility for the fast-sale/POS table.

## Modified files
- `alrajhi_client/views/widgets/vouchers_widget.py`
- `alrajhi_client/views/widgets/pos_widget.py`
- `alrajhi_client/i18n/translator.py`
- `tools/phase112_voucher_pos_ui_guard.py`

## Voucher delete behavior
The vouchers toolbar now includes `🗑 Delete voucher`.

Deletion flow:
1. Requires a selected voucher.
2. Loads the voucher before deletion.
3. Shows a confirmation warning explaining that accounting effects will be reversed.
4. Calls `voucher_service.delete(voucher_id)`.
5. Refreshes the table after success.

This keeps the same accounting path already verified in phase105:
- reverse invoice paid amount;
- reverse customer/supplier balance;
- reverse cash/bank movement;
- audit log DELETE.

## POS column visibility behavior
The POS screen now includes `🧩 POS columns`.

Supported columns:
- Item
- Barcode
- Unit
- Quantity
- Price
- Total
- Available

Behavior:
- Each column can be shown/hidden from a checkable menu.
- The selection is persisted in `QSettings` under `pos/visible_columns`.
- The system prevents hiding every column at once.
- Reset columns restores the full default table.

## Tests executed
- `python -m compileall -q .`
- `python tools/vouchers_deep_accounting_test_phase105.py`
- `python tools/phase32_invoice_flow_guard.py`
- `python tools/verify_pos_localization_phase88.py`
- `python tools/invoice_phase108_integrity_guard.py`
- `python tools/manufacturing_flow_guard.py`
- `python tools/verify_dialog_buttonbox_integrity.py`
- `python tools/qt_signal_method_guard.py`
- `python tools/offline_widget_guard.py`
- `python tools/html_print_expansion_guard.py`
- `python tools/phase61_brand_print_dashboard_guard.py`
- `python tools/verify_phase89_secondary_localization.py`
- `python tools/phase112_voucher_pos_ui_guard.py`

## Result
PASS.
