# Phase 198 — Startup Circular Import Hotfix

## Problem
Application startup failed with:

```text
ImportError: cannot import name 'settings_service' from partially initialized module 'core.services.settings_service'
```

The failing chain was:

```text
warehouse_service
 -> inventory_operation_policy
 -> permission_service
 -> settings_service
 -> create_settings_gateway
 -> LocalSettingsGateway
 -> SettingsRepository
 -> database package eager imports
 -> expense_repo
 -> currency
 -> settings_service  # partially initialized
```

## Fix
`currency.py` no longer imports `settings_service` at module import time. It now resolves it lazily through `_settings_service()` only when currency preferences are actually needed.

`CurrencyManager` also no longer creates its currency gateway during module import. The gateway is now lazy through the `gateway` property.

## Files changed

```text
alrajhi_client/currency.py
tools/phase198_startup_circular_import_guard.py
```

## Guard
The guard simulates the reported import path with a lightweight PyQt5 `QSettings` stub and verifies:

- `warehouse_service` can import without the circular import.
- `settings_service` can import after that.
- `currency.py` does not import `settings_service` at module import time.
- `CurrencyManager.gateway` remains lazy after import.

## Validation

```text
python -m compileall -q alrajhi_client alrajhi_server
python tools/phase197_inventory_printing_bridge_guard.py
python tools/phase198_startup_circular_import_guard.py
```
