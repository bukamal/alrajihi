#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Guard for Phase 221 finance voucher document shell refactor."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / 'alrajhi_client'


def assert_contains(path: Path, needles: list[str]) -> None:
    text = path.read_text(encoding='utf-8')
    missing = [needle for needle in needles if needle not in text]
    if missing:
        raise AssertionError(f'{path.relative_to(ROOT)} missing: {missing}')


def main() -> int:
    voucher_tab = CLIENT / 'features' / 'vouchers' / 'voucher_editor_tab.py'
    expense_tab = CLIENT / 'features' / 'finance' / 'documents' / 'expense_document_tab.py'
    translator = CLIENT / 'i18n' / 'translator.py'

    assert_contains(voucher_tab, [
        'DocumentHeaderCard',
        'DocumentPanel',
        'SummaryPanel',
        'BottomActionBar',
        '_VoucherMetricCard',
        'voucher_identity_panel',
        'voucher_party_link_panel',
        'voucher_payment_panel',
        'voucher_summary_panel',
        'currency.format_base_amount',
        'finance_operation_policy.OP_VOUCHER_PRINT',
        'voucher_service.add',
        'voucher_service.update',
    ])
    assert_contains(expense_tab, [
        'OP_EXPENSE_CREATE',
        'OP_EXPENSE_EDIT',
        'OP_EXPENSE_PRINT',
        'header_save_btn',
        'bottom_save_btn',
    ])
    assert_contains(translator, [
        '_PHASE221_VOUCHER_SHELL_TRANSLATIONS',
        'voucher_document_subtitle',
        'voucher_metric_invoice_remaining',
        'voucher_shell_unified',
    ])
    print('phase221_voucher_document_shell_guard passed')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
