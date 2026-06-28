# Phase 406 — Basit Shell Chrome

This phase applies the Basit-inspired visual system to the application shell itself.

## Scope

- Main icon menu bar.
- Shared global action bar.
- Workspace tab cards.
- Global fallback QSS for shell chrome.

## Visual rules

- Menu buttons use strong Basit blue.
- Home/open/selected states use Basit yellow with red emphasis.
- The shared action bar uses the same Basit toolbar background and button geometry.
- Primary action-bar commands use the Basit red total/action accent.
- Workspace tabs use blue selected tabs and a yellow underline.

## Files

- `alrajhi_client/views/main_window.py`
- `alrajhi_client/shell/unified_action_bar.py`
- `alrajhi_client/shell/tab_workspace.py`
- `alrajhi_client/theme/brand.py`
- `alrajhi_client/theme/qss.py`
