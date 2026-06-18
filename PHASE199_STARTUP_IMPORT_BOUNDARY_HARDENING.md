# Phase 199 — Startup Import Boundary Hardening

## Goal

Phase 198 fixed the immediate circular import in `currency.py`. Phase 199 hardens the root cause: package initializers in `database`, `database.repositories`, and `database.dao` were eager-importing many unrelated repositories/DAOs during startup.

That meant importing one focused module such as `database.repositories.settings_repo` could also import expense/currency/reporting code before `settings_service` had completed initialization.

## Changes

- Converted `alrajhi_client/database/__init__.py` to a lazy public API using module `__getattr__`.
- Converted `alrajhi_client/database/repositories/__init__.py` to lazy exports.
- Converted `alrajhi_client/database/dao/__init__.py` to lazy exports and lazy DAO singleton resolution.
- Kept backward-compatible names such as:
  - `from database import UserRepository`
  - `from database import item_dao`
  - `from database.repositories import SettingsRepository`
  - `from database.dao import invoice_dao`
- Added `tools/phase199_startup_import_boundary_guard.py` to prevent reintroducing eager imports.

## Why this matters

The settings bootstrap path should only initialize settings-related code. It should not pull in expense/currency/reporting/manufacturing/warehouse modules unless a caller actually needs those names.

## Validation

Run:

```bash
python tools/phase199_startup_import_boundary_guard.py
python -m compileall -q alrajhi_client alrajhi_server
```
