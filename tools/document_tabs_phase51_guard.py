#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Guard Phase 51 voucher document tabs.

Receipt/payment/expense vouchers must be first-class document tabs, not merely
legacy dialogs embedded in a tab.  Persistence stays behind VoucherService and
printing stays behind the unified printing service.
"""
from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VOUCHER_TAB = ROOT / 'alrajhi_client' / 'features' / 'vouchers' / 'voucher_editor_tab.py'
COMPONENTS = ROOT / 'alrajhi_client' / 'features' / 'vouchers' / 'components'
VOUCHERS_WIDGET = ROOT / 'alrajhi_client' / 'views' / 'widgets' / 'vouchers_widget.py'
MAIN = ROOT / 'alrajhi_client' / 'views' / 'main_window.py'


def main() -> int:
    errors: list[str] = []
    paths = [VOUCHER_TAB, VOUCHERS_WIDGET, MAIN] + list(COMPONENTS.glob('*.py'))
    for path in paths:
        if not path.exists():
            errors.append(f'missing {path.relative_to(ROOT)}')
            continue
        try:
            ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
        except SyntaxError as exc:
            errors.append(f'syntax error in {path.relative_to(ROOT)}:{exc.lineno}: {exc.msg}')

    text = VOUCHER_TAB.read_text(encoding='utf-8') if VOUCHER_TAB.exists() else ''
    required = [
        'class VoucherEditorTab(BaseDocumentTab)',
        'VoucherHeaderPanel',
        'VoucherLinkPanel',
        'VoucherPaymentPanel',
        'VoucherActionsPanel',
        'voucher_service.add',
        'voucher_service.update',
        'printing_service.voucher_preview',
        'printing_service.voucher_pdf',
        'def workspace_save',
        'def workspace_print',
        'def workspace_export',
    ]
    for token in required:
        if token not in text:
            errors.append(f'VoucherEditorTab missing token: {token}')

    forbidden = ['DialogDocumentTab', 'VoucherDialog', 'DatabaseConnection', '.execute(']
    for token in forbidden:
        if token in text:
            errors.append(f'VoucherEditorTab still contains forbidden token: {token}')

    for name in ('voucher_header.py', 'voucher_link.py', 'voucher_payment.py', 'voucher_actions.py'):
        if not (COMPONENTS / name).exists():
            errors.append(f'missing voucher component: {name}')

    widget_text = VOUCHERS_WIDGET.read_text(encoding='utf-8') if VOUCHERS_WIDGET.exists() else ''
    if 'main.open_quick_voucher' not in widget_text:
        errors.append('VouchersWidget no longer routes add/edit to workspace voucher tabs')
    main_text = MAIN.read_text(encoding='utf-8') if MAIN.exists() else ''
    if 'from features.vouchers import VoucherEditorTab' not in main_text or 'def open_quick_voucher' not in main_text:
        errors.append('main_window missing voucher document tab integration')

    if errors:
        print('Phase 51 voucher document tabs guard failed:')
        for error in errors:
            print(f' - {error}')
        return 1
    print('Phase 51 voucher document tabs guard passed.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
