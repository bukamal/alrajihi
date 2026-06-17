# GATEWAY PHASE 91 - Import Path Hotfix

## Problem
Running the app as:

```bash
python3 alrajhi_client/main.py
```
failed with:

```text
ModuleNotFoundError: No module named 'alrajhi_client'
```

because several secondary widgets used absolute package imports like:

```python
from alrajhi_client.i18n import translate, qt_layout_direction
```

This does not work in the project's current direct-script launch mode.

## Fix
Replaced absolute i18n imports with the project's existing import style:

```python
from i18n import translate, qt_layout_direction
```

## Files changed
- `alrajhi_client/views/widgets/users_widget.py`
- `alrajhi_client/views/widgets/branches_widget.py`
- `alrajhi_client/views/widgets/audit_log_widget.py`
- `alrajhi_client/views/widgets/categories_widget.py`
- `alrajhi_client/views/widgets/offline_queue_widget.py`
- `alrajhi_client/views/widgets/monitoring_widget.py`

## Guard added
- `tools/verify_no_absolute_alrajhi_imports.py`

## Validation
- `python3 tools/verify_no_absolute_alrajhi_imports.py` ✅
- `python3 -m compileall -q alrajhi_client` ✅
