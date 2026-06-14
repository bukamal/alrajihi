# GATEWAY PHASE 85 – Init Order + MainWindow Error Page Hotfix

## Scope
This hotfix addresses the startup crash reported after Phase 84.

## Fixed issues

### 1. ItemsWidget superclass initialization order
`ItemsWidget.__init__()` called `self.setLayoutDirection(...)` before `super().__init__(parent)`.

This is invalid for PyQt widgets and caused:

```text
RuntimeError: super-class __init__() of type ItemsWidget was never called
```

Fix:
- Moved `self.setLayoutDirection(qt_layout_direction())` after `super().__init__(parent)`.

### 2. MainWindow fallback error page
The error-page fallback referenced `PAGE_META`, but the current localized implementation uses `PAGE_META_KEYS` plus helper functions.

This caused:

```text
NameError: name 'PAGE_META' is not defined
```

Fix:
- Replaced direct `PAGE_META` access with `page_title(page_key)`.

### 3. Added guard
Added:

```text
tools/verify_widget_init_order.py
```

It detects widget methods such as `setLayoutDirection`, `setStyleSheet`, `setWindowTitle`, etc. being called before `super().__init__()`.

## Validation
Passed:

- `python3 tools/verify_widget_init_order.py`
- `python3 -m compileall -q alrajhi_client tools`
- `python3 tools/verify_language_foundation.py`
- `python3 tools/verify_language_migration_phase77.py`
- `python3 tools/verify_language_phase78_sales_purchases_returns.py`
- `python3 tools/verify_language_phase79_inventory_items.py`
- `python3 tools/verify_language_phase80_manufacturing.py`
- `python3 tools/verify_language_phase81_finance.py`
- `python3 tools/verify_language_phase82_reports_printing.py`
- `python3 tools/verify_language_phase84_settings_cleanup.py`

## Functional impact
No business logic was changed.

This is a startup/runtime stability hotfix only.
