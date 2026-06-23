# Phase 354 — Branded Tabs, Menu & Action Bar

## Scope
This phase applies the logo-inspired brand identity to the daily shell chrome, not only to splash/login/activation.

## Implemented
- Added `theme.shell_identity` as the PyQt-free contract for shell tokens, object names and QSS markers.
- Added `shell.tab_label_policy` so every real workspace tab shows a visible main/sub label:
  - `رئيسي · <workspace>` for main workspace pages.
  - `فرعي · <document>` for nested document/sub-workspace tabs.
- Dashboard remains a fixed surface and is still never opened as a tab.
- Updated `TabbedWorkspace` to apply branded labels, tooltips and tab metadata.
- Updated `UnifiedActionBar` with branded action hierarchy:
  - Save/Print as primary actions.
  - New/Refresh/Export/Quick Open as secondary actions.
  - Theme/Screenshot/Alerts/User as utility actions.
- Updated icon menu chrome with brand tokens and stronger menu hover/selection states.
- Added QSS coverage for branded tab cards, menu buttons and action-bar chips.

## Guard
`tools/phase354_branded_shell_runtime_guard.py`

## Tests
`tests/test_phase354_branded_shell_runtime.py`
