# Phase 226 — Printing Runtime Loader Hardening

## Problem

The Windows PyInstaller build still failed during startup with:

```text
ModuleNotFoundError: No module named 'printing.print_templates'
```

The traceback showed that `printing/__init__.py` eagerly imported `print_manager`, which then loaded `.print_templates` before the requested `printing.printing_service` submodule could finish importing. In frozen one-dir builds, `alrajhi_client/printing` is exposed as top-level `printing` because the build passes `--paths alrajhi_client`.

## Fix

- Made `alrajhi_client/printing/__init__.py` lazy via `__getattr__`.
- Added `alrajhi_client/printing/_template_loader.py`.
- Routed `print_manager.py` and `printing_service.py` through `require_template()` instead of direct `.print_templates` imports.
- Added PyInstaller hooks:
  - `build/hooks/hook-printing.py`
  - `build/hooks/hook-alrajhi_client.printing.py`
- Added explicit `--additional-hooks-dir build/hooks`.
- Added explicit `--collect-data` and `--add-data` coverage for `print_templates.py` in both top-level and package-qualified locations.
- Added `tools/phase226_printing_runtime_loader_guard.py`.

## Result

Startup no longer depends on eager import of `print_manager` from `printing.__init__`. The full template module is still collected for normal printing, and a safe fallback renderer prevents the application from crashing if a packaging tool misses the template module again.
