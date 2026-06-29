# Phase 442 — Project-wide Visual Style Cleanup Sweep

This phase continues the gradual visual-style debt cleanup started in Phase 440 and Phase 441.

## Scope

- Migrated small dialog/workspace surfaces away from hard-coded local `setStyleSheet()` calls.
- Added central QSS roles for camera preview, table-column headers and semantic error cards.
- Raised project visual identity phases to 442.
- Preserved business logic, data models, permissions, printing, barcode scanning and shell navigation.

## Migrated surfaces

- `views/dialogs/barcode_camera_dialog.py`
- `views/dialogs/column_contract_customizer.py`
- `views/widgets/offline_queue_widget.py`
- `views/main_window.py` remote page load error surface

## Verification

Run:

```bash
python tools/phase442_projectwide_visual_style_cleanup_guard.py
pytest tests/test_phase442_projectwide_visual_style_cleanup.py
```

The audit outputs are written to:

- `tools/audit_outputs/legacy_visual_style_sweep.csv`
- `tools/audit_outputs/legacy_visual_style_sweep_summary.json`
- `tools/audit_outputs/projectwide_visual_style_cleanup_summary.json`
