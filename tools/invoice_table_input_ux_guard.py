# -*- coding: utf-8 -*-
"""Phase 62 guard: invoice grid and SmartTable keyboard/input UX.

This guard protects the UX requirements that triggered Phase 62:
- invoice lines must remain a keyboard-first extended grid;
- bottom actions/columns must not regress to ad-hoc dialogs;
- SmartTableView must expose enterprise shortcuts and row density controls.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def require(path: str, needle: str, errors: list[str], label: str | None = None) -> None:
    text = (ROOT / path).read_text(encoding='utf-8')
    if needle not in text:
        errors.append(f"{path}: missing {label or needle!r}")


def main() -> int:
    errors: list[str] = []
    invoice = 'alrajhi_client/views/dialogs/invoice_dialog.py'
    smart = 'alrajhi_client/ui/smart_table_view.py'

    for needle in [
        'invoice_grid_shortcuts_label',
        'Qt.Key_Insert',
        'Ctrl+D',
        'duplicate_selected_line',
        'Qt.Key_F4',
        'Qt.Key_L',
        'fit_columns_to_view',
    ]:
        require(invoice, needle, errors)

    for needle in [
        '_install_enterprise_shortcuts',
        'Ctrl+Shift+C',
        'Ctrl+Alt+F',
        'Ctrl+Shift+S',
        'set_density',
        'visible_columns',
        'current_source_row',
        'row_density',
    ]:
        require(smart, needle, errors)

    if errors:
        print('Phase 62 invoice/table input UX guard failed:')
        for err in errors:
            print(f' - {err}')
        return 1
    print('Phase 62 invoice/table input UX guard passed.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
