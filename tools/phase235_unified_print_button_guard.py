# -*- coding: utf-8 -*-
"""Phase 235 guard: all visible print buttons use unified print, no PDF buttons.

The project may keep PDF-capable backend helpers for compatibility or internal
printing_service rendering, but screens must not expose separate PDF actions from
invoice/return/barcode/table/report print controls.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

FORBIDDEN_UI_PATTERNS = [
    # No explicit PDF actions in UI/menu code.
    re.compile(r"addAction\([^\n]*(export_pdf|save_pdf|PDF|pdf)[^\n]*\)", re.IGNORECASE),
    re.compile(r"QPushButton\([^\n]*(export_pdf|save_pdf|PDF|pdf)[^\n]*\)", re.IGNORECASE),
    re.compile(r"QAction\([^\n]*(export_pdf|save_pdf|PDF)[^\n]*\)", re.IGNORECASE),
]

UI_ROOTS = [
    ROOT / 'alrajhi_client' / 'features',
    ROOT / 'alrajhi_client' / 'views',
    ROOT / 'alrajhi_client' / 'ui',
]

ALLOW_FILES = {
    # Settings may retain stored report/export booleans; this is not a visible print button contract.
    str(ROOT / 'alrajhi_client' / 'views' / 'widgets' / 'settings_widget.py'),
    # printing_service owns PDF backend compatibility, not UI buttons.
    str(ROOT / 'alrajhi_client' / 'printing' / 'printing_service.py'),
}


def iter_py_files():
    for base in UI_ROOTS:
        if not base.exists():
            continue
        for path in base.rglob('*.py'):
            if '__pycache__' in path.parts:
                continue
            yield path


def main() -> int:
    failures: list[str] = []
    for path in iter_py_files():
        if str(path) in ALLOW_FILES:
            continue
        text = path.read_text(encoding='utf-8')
        for pattern in FORBIDDEN_UI_PATTERNS:
            for match in pattern.finditer(text):
                line_no = text[:match.start()].count('\n') + 1
                failures.append(f"{path.relative_to(ROOT)}:{line_no}: {match.group(0).strip()}")

    transaction_tab = ROOT / 'alrajhi_client' / 'features' / 'transactions' / 'transaction_document_tab.py'
    tx = transaction_tab.read_text(encoding='utf-8')
    for forbidden in ('transaction_pdf', 'transaction_preview', 'transaction_save_and_print'):
        if forbidden in tx:
            failures.append(f"transaction_document_tab.py still exposes {forbidden} in document actions")
    if '("print", self.workspace_print)' not in tx:
        failures.append('transaction_document_tab.py does not expose the single unified print action')

    invoice_actions = (ROOT / 'alrajhi_client' / 'features' / 'invoices' / 'components' / 'invoice_actions.py').read_text(encoding='utf-8')
    if 'save_invoice_pdf()' in invoice_actions:
        failures.append('InvoiceActionsComponent.export still calls save_invoice_pdf()')

    batch = (ROOT / 'alrajhi_client' / 'views' / 'dialogs' / 'batch_print_dialog.py').read_text(encoding='utf-8')
    for forbidden in ('barcode_labels_pdf', 'barcode_labels_png', "printer_info.type.value == 'pdf'", "printer_info.type.value == 'image'"):
        if forbidden in batch:
            failures.append(f'batch_print_dialog.py still exposes legacy barcode output path: {forbidden}')
    if 'barcode_labels_print(' not in batch:
        failures.append('batch_print_dialog.py does not use barcode_labels_print()')

    item_editor = (ROOT / 'alrajhi_client' / 'features' / 'items' / 'item_editor_tab.py').read_text(encoding='utf-8')
    if 'barcode_labels_print_settings' not in item_editor:
        failures.append('item_editor_tab.py print button does not use project barcode print settings')

    if failures:
        raise AssertionError('Phase 235 unified print guard failed:\n' + '\n'.join(failures[:80]))
    print('Phase 235 unified print button guard passed.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
