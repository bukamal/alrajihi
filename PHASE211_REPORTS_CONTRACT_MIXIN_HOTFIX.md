# Phase 211 — Reports Contract Mixin Hotfix

## Problem

CI failed on:

```text
python tools/reports_contract_check.py
AssertionError: ReportsWidget calls missing private methods: ['_refresh_phase36_reports']
```

`ReportsWidget` inherits `ReportsPhase36Mixin`, where `_refresh_phase36_reports()` is implemented, but the contract checker intentionally reads only methods declared directly on `ReportsWidget`. Because `ReportsWidget.refresh_report()` calls `self._refresh_phase36_reports(...)`, the static check treated the method as missing.

## Fix

Added an explicit compatibility wrapper to:

```text
alrajhi_client/views/widgets/reports_widget.py
```

```python
def _refresh_phase36_reports(self, start, end, display_curr):
    return super()._refresh_phase36_reports(start, end, display_curr)
```

The report implementation remains in `ReportsPhase36Mixin`; no report logic was duplicated.

## Validation

```text
python tools/reports_contract_check.py
python -m compileall -q alrajhi_client alrajhi_server
```
