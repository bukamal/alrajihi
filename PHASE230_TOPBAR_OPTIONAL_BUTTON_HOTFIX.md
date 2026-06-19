# Phase 230 — Top-bar Optional Button Hotfix

## Problem

After Phase 228/229, the global top-bar refresh button was intentionally removed.
`ModernTopBar` kept `refresh_btn = None` as a compatibility placeholder, but
`MainWindow.setup_topbar_buttons()` used `hasattr(self.top_bar, 'refresh_btn')`.
Because the attribute exists even when it is `None`, startup failed with:

```text
AttributeError: 'NoneType' object has no attribute 'clicked'
```

## Fix

`MainWindow.setup_topbar_buttons()` now uses `getattr(..., None)` and connects
only real button objects:

```python
refresh_btn = getattr(self.top_bar, 'refresh_btn', None)
if refresh_btn is not None:
    refresh_btn.clicked.connect(self.refresh_current_view)
```

The same safe pattern is used for `screenshot_btn`.

## Validation

Added:

```text
tools/phase230_topbar_optional_buttons_guard.py
```

The guard prevents direct `.clicked` access on optional top-bar buttons and
prevents reverting to `hasattr()` for removed compatibility placeholders.
