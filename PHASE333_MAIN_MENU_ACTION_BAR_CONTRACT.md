# Phase 333 — Main Menu and Action Bar Contract

This phase upgrades the UI unification foundation from Phase 331/332 by moving
main-shell command visibility and top navigation structure into registry-owned
contracts.

## Scope

- Introduced `ACTION_SPECS` in `workspace.registry.ui_manifest`.
- Introduced `MAIN_NAVIGATION_MENUS` with menu entries, page targets, callback
  targets, icons, shortcuts and admin-only flags.
- Added effective per-page action resolution so normal workspaces receive their
  workspace actions plus utility actions.
- Dashboard now shows only the allowed minimal utility strip requested by UX:
  refresh, theme, screenshot and user.  It does not show alert, new, save,
  print, export or quick-open.
- `UnifiedActionBar` can now hide/show every button from a contract instead of
  relying on a fixed global row.
- `MainWindow.setup_menus()` now consumes `navigation_menus()` instead of owning
  a long manual navigation definition.
- `MainWindow` applies the action-bar contract whenever the active tab/page
  changes, including document tabs.

## Guarantees

- Page visibility is still governed by `module_visibility_policy`.
- Main menu entries that point to pages must point to registered pages.
- Callback-only menu entries are resolved in `MainWindow._menu_callback_map()`.
- Browser HTML printing remains unchanged.
- RTL/LTR, network/API mode, module enable flags and user permissions are not
  bypassed.

## Next phase

Phase 334 should introduce the universal column contract and start applying it
to invoices, apparel and high-risk operational tables.
