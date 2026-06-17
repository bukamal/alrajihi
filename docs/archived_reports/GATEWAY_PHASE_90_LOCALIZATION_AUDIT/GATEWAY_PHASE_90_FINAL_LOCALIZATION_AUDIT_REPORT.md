# GATEWAY PHASE 90 — Final Localization Audit
## Scope
Final localization audit after Phases 76–89. This phase does not alter business logic; it adds an auditable localization coverage report and verification guard.
## Summary
- Python files scanned: **214**
- Translation keys total: **1165**
- Translation keys used in code: **1076**
- Used keys missing from dictionaries: **0**
- `ftranslate` references: **0**
- Parse errors: **0**

## Hardcoded string findings
- possible_ui_or_message: **1020**
- arabic_literal: **867**
- other_literal: **330**
- likely_ui: **229**

## Translation coverage by dictionary
- ar: **100.0%** of known key universe
- de: **100.0%** of known key universe
- en: **100.0%** of known key universe

## Top files still containing UI-like direct strings
- `alrajhi_client/views/widgets/reports_widget.py`: **220**
- `alrajhi_client/theme/qss.py`: **126**
- `alrajhi_client/printing/print_templates.py`: **88**
- `alrajhi_client/database/dao/manufacturing_dao.py`: **87**
- `alrajhi_client/database/connection.py`: **74**
- `alrajhi_client/views/widgets/modern_ui.py`: **70**
- `alrajhi_client/views/dialogs/item_dialog.py`: **60**
- `alrajhi_client/views/widgets/dashboard_widget.py`: **60**
- `alrajhi_client/views/widgets/settings_widget.py`: **57**
- `alrajhi_client/database/dao/inventory_ledger_dao.py`: **57**
- `alrajhi_client/main.py`: **46**
- `alrajhi_client/views/main_window.py`: **46**
- `alrajhi_client/views/widgets/invoices_widget.py`: **44**
- `alrajhi_client/views/dialogs/invoice_dialog.py`: **43**
- `alrajhi_client/core/server_control.py`: **40**
- `alrajhi_client/views/modern_topbar.py`: **36**
- `alrajhi_client/database/repositories/warehouse_repo.py`: **34**
- `alrajhi_client/printing/printing_service.py`: **31**
- `alrajhi_client/database/schema_manager.py`: **28**
- `alrajhi_client/views/dialogs/batch_print_dialog.py`: **27**

## High priority next cleanup order
1. `alrajhi_client/views/widgets/reports_widget.py` — 220 candidate strings
2. `alrajhi_client/theme/qss.py` — 126 candidate strings
2. `alrajhi_client/printing/print_templates.py` — 88 candidate strings
2. `alrajhi_client/database/dao/manufacturing_dao.py` — 87 candidate strings
2. `alrajhi_client/database/connection.py` — 74 candidate strings
2. `alrajhi_client/views/widgets/modern_ui.py` — 70 candidate strings
2. `alrajhi_client/views/dialogs/item_dialog.py` — 60 candidate strings
2. `alrajhi_client/views/widgets/dashboard_widget.py` — 60 candidate strings
2. `alrajhi_client/views/widgets/settings_widget.py` — 57 candidate strings
2. `alrajhi_client/database/dao/inventory_ledger_dao.py` — 57 candidate strings

## Artifacts
- `GATEWAY_PHASE_90_LOCALIZATION_AUDIT/hardcoded_strings_all.csv`
- `GATEWAY_PHASE_90_LOCALIZATION_AUDIT/hardcoded_strings_priority.csv`
- `GATEWAY_PHASE_90_LOCALIZATION_AUDIT/translation_key_audit.json`
- `GATEWAY_PHASE_90_LOCALIZATION_AUDIT/ftranslate_refs.csv`

## Result
Audit completed: no missing used translation keys, no ftranslate leftovers, no parse errors. Remaining hardcoded strings are listed for staged cleanup.
