# Phase 425 — Editable Grid Enter Preserve Hotfix

## Problem

Runtime testing showed that Enter navigation inside editable cells could still
wipe values.  The remaining cause was not row lifecycle or column routing: the
central keyboard policy still called `commitData(editor)` every time Enter was
pressed inside an active editor.

That is unsafe because some delegates and Qt default editors can serialize an
untouched editor as an empty string.  Opening a cell and pressing Enter must be
navigation, not a write operation.

## Fix

`StandardTableKeyboardMixin` now tracks whether the active editor was actually
changed by the operator.

Tracked editors include:

- `QLineEdit` through `textEdited`
- `QComboBox` through `activated` and `currentIndexChanged`
- `QSpinBox` / `QDoubleSpinBox` through `valueChanged`
- `QTextEdit` / `QPlainTextEdit` through `textChanged`

The Enter handler now uses:

`_standard_commit_enter_editor_if_modified(editor)`

instead of calling `commitData(editor)` directly.

If the editor was not modified, it is closed for navigation without writing
anything to the model.  If the editor was modified, it is committed normally.

## Runtime rule

Enter has two modes:

1. Active editor unchanged: close editor, preserve model value, navigate.
2. Active editor changed: commit changed value, close editor, navigate.

This prevents accidental clearing while preserving normal fast entry.

## Verification

Added:

- `alrajhi_client/workspace/quality/editable_grid_enter_preserve_contract.py`
- `tools/phase425_editable_grid_enter_preserve_guard.py`
- `tests/test_phase425_editable_grid_enter_preserve.py`

The release gate registers Phase 425 as a UI hotfix.
