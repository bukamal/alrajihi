# GATEWAY PHASE 116 — Context-Aware Global Search

## Scope
Implemented page-aware global search under the main navigation bar.

## Behavior
- Dashboard: global search is hidden.
- Supported pages: global search is shown with a page-specific placeholder.
- The search value is forwarded to each widget through `set_global_filter(text)` where available.
- Legacy widgets with `search_edit`, toolbar search fields, or POS barcode input are handled safely.
- Search context resets when switching pages to avoid stale filters leaking between screens.

## Implemented paths
- `alrajhi_client/views/main_window.py`
- `alrajhi_client/views/widgets/base_widget.py`
- `alrajhi_client/views/widgets/invoices_widget.py`
- `alrajhi_client/views/widgets/pos_widget.py`
- Search adapters for vouchers, customers, suppliers, categories, branches, audit log, returns, manufacturing, warehouses, cashboxes, users, offline queue, monitoring.
- `alrajhi_client/i18n/translator.py`

## Language coverage
Arabic, German, and English placeholders were added for the new contextual search states.

## Tests
- `python3 -m compileall -q alrajhi_client`
- `phase116_static_guard`: PASS
- `tools/phase32_invoice_flow_guard.py`: PASS
- `tools/qt_signal_method_guard.py`: PASS
- `tools/verify_phase89_secondary_localization.py`: PASS
- `tools/offline_widget_guard.py`: PASS

## Result
PASS.
