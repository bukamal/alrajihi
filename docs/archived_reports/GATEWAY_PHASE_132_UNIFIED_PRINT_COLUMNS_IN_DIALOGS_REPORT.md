# Phase132 — Unified Print Buttons + In-Dialog Column Controls

## Scope
- Route table/page print buttons outside dialogs through the central `printing.printing_service` report path.
- Add column customization buttons inside invoice dialogs and return dialogs.
- Preserve existing context-menu column customization.
- Preserve Arabic/English/German translation keys by using existing `translate()` keys.

## Files changed
- `alrajhi_client/views/custom_table_view.py`
- `alrajhi_client/views/widgets/components/table_toolbar.py`
- `alrajhi_client/views/dialogs/invoice_dialog.py`
- `alrajhi_client/views/widgets/returns_widget.py`

## Print unification
`CustomTableView.print_table(mode)` now supports:
- preview
- browser / open HTML
- direct print
- PDF export

`TableToolbar.set_table()` installs the unified print menu automatically for page-level table print buttons. Specialized pages may still override the menu after `set_table()`.

## Column controls inside dialogs
Added visible `columns` buttons inside:
- sales invoice dialog line table
- purchase invoice dialog line table
- sales return dialog line table
- purchase return dialog line table

The buttons use the same saved visibility/header-state paths already used by the context menus.

## Localization
All added UI uses existing i18n keys:
- `columns`
- `reset_columns`
- `preview_in_app`
- `open_html_browser`
- `direct_print`
- `export_pdf`

These are already present for Arabic, German, and English.

## Validation
- `python3 -m compileall -q alrajhi_client` passed.
