# Phase 98 – Unified Barcode Printing + Settings

## Scope
- Unified single barcode printing and batch barcode printing through `printing.printing_service`.
- Added barcode printing defaults to Printing Settings.
- Kept barcode value generation/validation logic unchanged.

## Changes
- `printing/printing_service.py`
  - Added `barcode_label_options()`.
  - Added `barcode_labels_html()`.
  - Added `barcode_labels_print()`.
  - Added `barcode_labels_pdf()`.
- `core/services/settings_service.py`
  - Added persistent barcode print settings:
    - default printer
    - label size
    - symbology
    - default copies
    - PDF columns
    - show company/name/price/barcode text
- `views/widgets/settings_widget.py`
  - Added Barcode Printing Settings card inside the Printing tab.
- `views/dialogs/batch_print_dialog.py`
  - Loads defaults from Printing Settings.
  - Uses unified `printing_service` for PDF and system printer output.
- `views/widgets/items_widget.py`
  - Single barcode print now opens the same unified barcode print dialog used by batch printing.

## Validation
- `python3 -m compileall -q alrajhi_client` passed.
- `tools/verify_phase98_barcode_printing_unified.py` passed.

## Notes
- Serial thermal printing remains supported via `ThermalPrinter` because it uses ESC/POS commands directly.
- PDF/system-printer label output now routes through the unified HTML print service.
