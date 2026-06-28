# Phase 426 — Editable Grid Enter Destination Focus Hotfix

## Problem

Phase 425 fixed one half of the Enter-clearing bug: it stopped committing an untouched source editor.

The remaining symptom was different: after Enter moved to the next cell, the destination editor was opened automatically. Some delegates can write an empty/default editor state when that newly reached editor is closed, so the **cell Enter moved to** could be cleared even though the operator did not edit it.

## Decision

Enter is navigation, not automatic editing.

After Phase 426:

- Enter from an open editor closes/commits only when truly modified, then selects the destination cell.
- The destination cell is **not auto-opened** by Enter navigation.
- Enter on a focused non-editing cell moves to the next semantic cell instead of opening the current editor.
- Typing, F2/double-click, and explicit Qt edit triggers still open editors normally.

## Files

- `alrajhi_client/ui/table_keyboard_policy.py`
- `alrajhi_client/workspace/quality/editable_grid_enter_destination_focus_contract.py`
- `tools/phase426_editable_grid_enter_destination_focus_guard.py`
- `tests/test_phase426_editable_grid_enter_destination_focus.py`

## Expected runtime behavior

1. Focus a cell that already has a value.
2. Press Enter.
3. Focus moves to the next semantic cell.
4. The destination value remains unchanged.
5. Press Enter again.
6. Focus moves again; no destination cell is cleared.
7. Type text/numbers in a focused cell.
8. Qt opens the editor and the value can be changed intentionally.

## Scope

This phase does not change financial logic, row lifecycle, or delegates. It changes the navigation contract so delegates are not opened unintentionally by Enter movement.
