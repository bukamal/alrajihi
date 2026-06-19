# Phase 215 — Settings Workspace Consolidation

## Goal
Expose the unified settings contracts that were added across the project in a visible Settings workspace section, instead of leaving critical switches hidden in `SettingsService` keys.

## Changes

- Added a new Settings tab: **Unified Contracts**.
- The tab controls module enable switches for:
  - Restaurant
  - Manufacturing
  - Inventory / warehouses
  - Finance
  - Reports
  - Users
  - Parties
  - Categories
  - Branches
- Added centralized operation switches for:
  - POS checkout / suspend / receipt printing
  - Restaurant checkout / kitchen send / receipt printing / kitchen ticket printing
  - Inventory transfer creation and inventory document printing
  - Manufacturing document printing
  - Report export
  - Expense creation
  - Voucher creation
- Added barcode contract settings:
  - scanner minimum length
  - numeric exact mode
  - material auto barcode generation
  - default material barcode symbology
- Added touch-density and default-payment controls for POS and Restaurant.
- Added Arabic, German, and English translation keys for the new section.

## Files changed

- `alrajhi_client/views/widgets/settings_widget.py`
- `alrajhi_client/i18n/translator.py`
- `tools/phase215_settings_workspace_consolidation_guard.py`

## Validation

Executed successfully:

```bash
python -m compileall -q alrajhi_client alrajhi_server
python tools/phase212_runtime_stabilization_guard.py
python tools/reports_contract_check.py
python tools/phase214_reports_governance_guard.py
python tools/phase215_settings_workspace_consolidation_guard.py
```

## Notes

This phase does not remove the older detailed tabs. It adds a consolidated governance-oriented section so the new contracts can be managed in one place. Detailed per-domain settings can continue to evolve in their existing tabs.
