# Phase134 Return Dialog Column Control Hotfix

## Issue
Opening PurchaseReturnDialog failed with:

`AttributeError: 'PurchaseReturnDialog' object has no attribute '_install_return_line_column_controls'`

## Cause
The dialog initialization path referenced a dialog-local column-control method while the shared implementation existed as module helpers. Older/merged call-sites could still call `self._install_return_line_column_controls(...)`.

## Fix
- Kept the shared helper `_ret_install_return_line_column_controls(dialog, identity)` as the canonical implementation.
- Added PurchaseReturnDialog-compatible methods that delegate to the shared helper.
- Added a module-level fallback assignment to preserve compatibility with any older call-sites.
- Confirmed current PurchaseReturnDialog initialization calls the helper directly.

## Validation
- `python3 -m compileall alrajhi_client/views/widgets/returns_widget.py` passed.
- Static grep confirms compatibility method exists and direct helper call is present.

## Scope
No accounting, inventory, pricing, language, or schema logic was changed.
