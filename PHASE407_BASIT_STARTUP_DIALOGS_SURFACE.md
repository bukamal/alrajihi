# Phase 407 — Basit Startup & Dialogs Surface

This phase extends the Basit-inspired visual system to application entry and
system surfaces after dashboard, transactions, management, reports/settings and
shell chrome have already been aligned.

## Scope

- Startup splash screen.
- Login dialog.
- Main activation dialog.
- Paid module activation dialog.
- Base frameless dialog shell.
- Branded message boxes.

## What changed

- Added Basit-specific QSS selectors for startup/login/activation/dialogs.
- Marked splash/login/activation surfaces with Basit runtime properties.
- Marked all branded dialogs and message boxes with `basitDialogSurface`.
- Gave login fields/buttons explicit object names/properties consumed by QSS.
- Converted module activation success feedback to a branded message box.
- Preserved authentication, activation and validation logic; this phase is visual/structural only.

## Guard

- `tools/phase407_basit_startup_dialogs_surface_guard.py`
- `tests/test_phase407_basit_startup_dialogs_surface.py`
- `alrajhi_client/workspace/quality/basit_startup_dialogs_surface_contract.py`
