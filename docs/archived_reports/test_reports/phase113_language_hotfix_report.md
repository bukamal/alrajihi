# Phase113 Language Hotfix Report

## Scope
Verified and fixed localization coverage for UI controls introduced in Phase112:

- Voucher delete action
- POS column visibility button/menu
- Generic table column menu/reset action
- Table context menu labels used alongside column controls

## Findings
Phase112 already contained translation keys for:

- `delete_voucher`
- `delete_voucher_confirm`
- `voucher_deleted`
- `pos_columns_btn`
- `columns`
- `column_number`
- `reset_columns`

However, `alrajhi_client/views/custom_table_view.py` still had hardcoded Arabic context-menu labels:

- `🧩 الأعمدة`
- `↩️ إعادة ضبط الأعمدة`
- `📊 تصدير إلى Excel`
- `📄 طباعة`
- `📋 نسخ`

## Fix Applied
Updated `custom_table_view.py` to use `translate()` for all affected context-menu labels.

Added missing general-purpose translation keys:

- `copy`
- `openpyxl_missing`
- `save_report`
- `report`

Languages covered:

- Arabic
- German
- English

## Validation
Executed successfully:

- `compileall`
- `verify_phase92_controls_localization.py`
- `verify_pos_localization_phase88.py`
- `verify_phase89_secondary_localization.py`
- `phase112_voucher_pos_ui_guard.py`
- `qt_signal_method_guard.py`
- `offline_widget_guard.py`
- `vouchers_deep_accounting_test_phase105.py`

## Result
PASS. Phase112 UI additions are now localized consistently.
