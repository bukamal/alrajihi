# Phase 447 — Unified List Workspace Visual Template

This phase introduces a centralized visual template for repeated list/grid workspaces such as sales invoices, purchase invoices, returns, customers, suppliers, users, vouchers and generic management lists.

Scope:

- Adds Phase 447 visual tokens for list filter bars, action buttons, counters, tables and detail cards.
- Updates `TableToolbar` to expose semantic visual roles: `list_filter_bar`, `list_primary_action`, `list_danger_action`, `list_search_input`, and `list_counter`.
- Updates `BaseWidget` generic list screens to opt into `listWorkspaceVisualTemplatePhase = 447` and `list_table`.
- Extends `runtime_visual_polish` with `_apply_list_workspace_template()` so lazy-loaded list workspaces receive the list visual template after generic runtime roles are applied.
- Adds a central QSS block after the older Basit list rules so the new template overrides legacy heavy toolbar and table chrome.

Non-goals:

- No business logic changes.
- No database, API, printing, permissions, or routing changes.
- No editor-grid behavior changes.

Validation:

- `tools/phase447_unified_list_workspace_visual_template_guard.py`
- `tests/test_phase447_unified_list_workspace_visual_template.py`
