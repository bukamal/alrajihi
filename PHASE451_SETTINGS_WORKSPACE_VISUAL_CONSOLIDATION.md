# Phase 451 — Settings Workspace Visual Consolidation

## Scope

This phase consolidates the visual identity of the Settings workspace.  It is a visual-only migration and does not change settings persistence, save handlers, SettingsService keys, backup/restore logic, language switching, or activation/network behavior.

## What changed

- Added Phase 451 settings visual tokens in `alrajhi_client/theme/brand.py`.
- Added centralized Settings QSS in `alrajhi_client/theme/qss.py` after Phase 450 document-editor rules.
- Marked `SettingsWidget` with `settingsVisualPhase = 451` and semantic roles:
  - `settings_workspace`
  - `settings_group_tabs`
  - `settings_leaf_tabs`
  - `settings_scroll_page`
  - `settings_card`
  - `settings_input`
  - `settings_note`
  - `settings_primary_action`
  - `settings_action`
  - `settings_table`
- Removed the Settings page-local stylesheet overlay and suppressed the old Basit settings surface override.
- Added runtime visual polish support for settings pages so lazy-loaded Settings receives the same roles.
- Added matching roles to `features/settings/settings_document_tabs.py` for settings document tabs opened independently.

## Guard

Run:

```bash
python tools/phase451_settings_workspace_visual_guard.py
pytest -q tests/test_phase451_settings_workspace_visual_consolidation.py
```
