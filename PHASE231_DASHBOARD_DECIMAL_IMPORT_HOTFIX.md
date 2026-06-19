# Phase 231 — Dashboard Decimal Import Hotfix

## Problem

After the dashboard simplification phases, the dashboard still rendered cash/project monetary summaries using `Decimal`, but `dashboard_widget.py` no longer imported it. Runtime refreshes failed with:

```text
NameError: name 'Decimal' is not defined
```

Affected paths:

- `DashboardWidget.refresh_all()` → `_refresh_project_card(...)`
- `_toggle_cash_visibility()` → `_render_cash_amounts(...)`

## Fix

Updated:

- `alrajhi_client/views/widgets/dashboard_widget.py`

Added:

```python
from decimal import Decimal
```

## Guard

Added:

- `tools/phase231_dashboard_decimal_import_guard.py`

The guard statically verifies that dashboard monetary rendering cannot use `Decimal` without importing it.

## Validation

Run:

```bash
python tools/phase231_dashboard_decimal_import_guard.py
python -m compileall -q alrajhi_client alrajhi_server
```
