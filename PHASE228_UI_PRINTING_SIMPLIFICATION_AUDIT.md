# Phase 228 — UI Printing Simplification Audit

## Scope

This phase implements the requested UX simplification and project-wide audit:

- Remove the dashboard top KPI card strip.
- Remove the dashboard monthly chart panel.
- Remove the global top search card from the shell.
- Reduce duplicated shell command buttons by keeping refresh in the unified action bar only.
- Keep printing under the central HTML printing boundary.
- Add a repeatable audit tool for the remaining UI/printing patterns.

## Dashboard changes

`alrajhi_client/views/widgets/dashboard_widget.py` no longer builds the top KPI card row or the monthly trend chart. The dashboard now starts with operational panels: quick actions, company info, cashbox panel, alerts, and brand/project panel.

The old `_build_kpi_grid()` method remains as a compatibility no-op so older code/tests do not fail if they call it.

## Global top search removal

`alrajhi_client/views/modern_topbar.py` no longer creates `GlobalSearchBox` or adds the global search card to the top utility strip.

`alrajhi_client/views/main_window.py` keeps the former global-search methods as no-op compatibility hooks, but no longer wires `textChanged` or `returnPressed` to a top search widget.

The settings UI no longer exposes the removed global-search checkbox as an active option and persists `ui/show_global_search = false`.

## Duplicate button cleanup

The topbar refresh button was removed because refresh already exists in `UnifiedActionBar` and through `F5`. This reduces one visible duplicate command path in every screen.

The remaining local document buttons are intentionally not blindly deleted because some document shells still need tab-local Save/Print/Export actions until a second action-placement normalization pass is done.

## Printing standardization

`alrajhi_client/printing/printing_service.py` now has a central `render_html()` dispatcher. It is the single mode router for:

- preview
- browser HTML preview
- direct print
- PDF export

Domain printing helpers should generate HTML and delegate to `render_html()` or its existing wrappers.

## Audit tools

Added:

- `tools/phase228_ui_printing_audit.py`
- `tools/phase228_ui_printing_guard.py`
- `tools/audit_outputs/phase228_ui_printing_audit.json`
- `tools/audit_outputs/PHASE228_UI_PRINTING_AUDIT.md`

Current audit result:

- high: 0
- medium: 0
- low: 24

The remaining low findings are potential local print buttons or local action surfaces. They are not release blockers, but they should be addressed in a future button-placement consolidation phase.

## Opinion after analysis

The requested removals are correct. The dashboard was becoming visually heavy and partly duplicated reports. The global top search was also conceptually weak because ERP searches are usually context-specific: item search, invoice search, party search, voucher search, etc. Keeping search inside each page is clearer.

Printing is largely in the right direction now: HTML templates and `printing_service` are the correct boundary. The remaining work is not about print rendering, but about action placement: every document should expose printing through one consistent menu/button contract rather than scattered custom buttons.

## Verification

Executed successfully:

```text
python tools/phase228_ui_printing_guard.py
python -m compileall -q alrajhi_client alrajhi_server
python tools/phase227_database_pyinstaller_guard.py
python tools/phase226_printing_runtime_loader_guard.py
python tools/phase224_windows_release_matrix_guard.py
python tools/phase223_finance_list_legacy_cleanup_guard.py
python tools/phase222_expense_document_shell_guard.py
python tools/phase221_voucher_document_shell_guard.py
python tools/phase220_party_document_shell_guard.py
python tools/phase219_projectwide_architecture_audit.py
python tools/reports_contract_check.py
python tools/advanced_runtime_test.py
```
