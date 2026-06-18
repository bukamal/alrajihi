# Phase 179 — POS Shift Disabled Enforcement

This hotfix completes POS shift-mode enforcement. When `pos/use_shifts=false`, POS sales are posted directly to the selected cashbox and shift operations are disabled consistently at policy, UI, and service levels.

## Changes

- `POSOperationPolicy` now treats `open_shift` and `close_shift` as disabled when `settings_service.pos_shifts_enabled()` is false.
- `POSWidget._apply_pos_operation_state()` keeps shift buttons hidden when shifts are disabled, even after later permission refreshes.
- `POSWidget.open_shift()` and `POSWidget.close_shift()` short-circuit when shifts are disabled.
- Existing `POSService.checkout()` behavior is preserved: it requires an open shift only when shifts are enabled; otherwise it clears `cart.shift_id`.
- Added `tools/phase179_pos_shift_disabled_guard.py`.
