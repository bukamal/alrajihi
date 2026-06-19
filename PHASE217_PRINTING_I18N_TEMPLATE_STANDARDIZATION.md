# Phase 217 — Printing i18n / Template Standardization

## Scope

This phase hardens the unified printing surface after invoices, returns, POS, restaurant, manufacturing, inventory, finance, and reports were routed through central printing bridges.

The goal is not to redesign templates. The goal is to remove user-facing hardcoded Arabic literals from the central printing path and enforce translation-driven preview/print/PDF titles and warnings.

## Main changes

### 1. `printing_service.py` now uses i18n keys

Added a local `_tr()` helper and migrated message boxes, preview titles, print titles, and save dialog labels from hardcoded Arabic strings to translation keys.

Examples:

- `print_no_content`
- `print_no_preview_content`
- `print_no_save_content`
- `print_preview_title`
- `print_dialog_title`
- `print_save_pdf`
- `invoice_preview_title`
- `restaurant_kitchen_ticket_print_title`
- `manufacturing_pick_ticket_print_title`
- `inventory_transfer_print_title`
- `report_preview_title`

### 2. `print_templates.py` removed remaining central Arabic labels

The central document templates now translate:

- tax number label
- commercial register label
- print date label
- QR/document code label
- receiver/accountant signature labels
- generic title map entries for categories and users

The only Arabic literal intentionally allowed in `print_templates.py` is `"نعم"` inside `_bool_setting()`, where it acts as a legacy boolean parser value and is not a UI label.

### 3. Translation keys added for Arabic, German, and English

Added Phase 217 translation block to:

```text
alrajhi_client/i18n/translator.py
```

Supported languages:

- Arabic
- German
- English

### 4. Guard added

Added:

```text
tools/phase217_printing_i18n_guard.py
```

The guard verifies:

- no Arabic UI literals in `printing_service.py`
- no Arabic UI literals in `print_templates.py`, except the boolean parser value
- central print labels use `_tr(...)`
- required translation keys exist

## Validation

Executed successfully:

```bash
python tools/phase217_printing_i18n_guard.py
python tools/phase216_legacy_dialog_audit_guard.py
python tools/phase215_settings_workspace_consolidation_guard.py
python tools/phase214_reports_governance_guard.py
python tools/phase212_runtime_stabilization_guard.py
python tools/reports_contract_check.py
python -m compileall -q alrajhi_client alrajhi_server
```

## Result

The central printable document path is now more consistent with the project's language model and is better prepared for multilingual printing in Arabic, English, and German.
