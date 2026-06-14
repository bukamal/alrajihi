# Phase 97 – Deleted Qt Widget Timer Hotfix

## Problem
A delayed `QTimer.singleShot` in `AutoSelectManager` could call `selectAll()` after a `QLineEdit` had already been destroyed, especially after closing transient dialogs such as barcode printing/export dialogs.

Error observed:

```text
RuntimeError: wrapped C/C++ object of type QLineEdit has been deleted
```

## Fix
Updated `alrajhi_client/utils.py`:

- Added `_is_qobject_alive(obj)` using `PyQt5.sip.isdeleted()` where available.
- Guarded delayed auto-select before scheduling and before execution.
- Caught `RuntimeError` around `selectAll()`.
- Added the same safety check to immediate `focus_first_input()` selection paths.

## Validation
- `python3 tools_verify_qtimer_deleted_widget_guard.py` ✅
- `python3 -m compileall -q alrajhi_client` ✅

## Scope
No business logic changed. This is a UI lifecycle-safety fix only.
