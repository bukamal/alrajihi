#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Guard for Phase 222 expense document shell refactor."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / 'alrajhi_client'


def assert_contains(path: Path, needles: list[str]) -> None:
    text = path.read_text(encoding='utf-8')
    missing = [needle for needle in needles if needle not in text]
    if missing:
        raise AssertionError(f'{path.relative_to(ROOT)} missing: {missing}')


def assert_not_contains(path: Path, needles: list[str]) -> None:
    text = path.read_text(encoding='utf-8')
    present = [needle for needle in needles if needle in text]
    if present:
        raise AssertionError(f'{path.relative_to(ROOT)} must not contain: {present}')


def main() -> int:
    expense_tab = CLIENT / 'features' / 'finance' / 'documents' / 'expense_document_tab.py'
    voucher_service = CLIENT / 'core' / 'services' / 'voucher_service.py'
    translator = CLIENT / 'i18n' / 'translator.py'

    assert_contains(expense_tab, [
        'class ExpenseDocumentTab(BaseDocumentTab)',
        'class ExpenseIdentityPanel(QWidget)',
        'ExpenseDocumentHeaderCard',
        'ExpenseDocumentPanel',
        'ExpenseSummaryPanel',
        'ExpenseBottomActionBar',
        '_ExpenseMetricCard',
        'expense_identity_panel',
        'expense_payment_panel',
        'expense_summary_panel',
        'finance_operation_policy.OP_EXPENSE_CREATE',
        'finance_operation_policy.OP_EXPENSE_EDIT',
        'finance_operation_policy.OP_EXPENSE_PRINT',
        'VoucherPaymentPanel',
        "data['type'] = 'expense'",
        "data['customer_id'] = None",
        "data['supplier_id'] = None",
        "data['invoice_id'] = None",
        'currency.format_base_amount',
        'voucher_service.add',
        'voucher_service.update',
    ])
    assert_not_contains(expense_tab, [
        'class ExpenseDocumentTab(VoucherEditorTab)',
        'VoucherLinkPanel',
        'header_panel.type_combo',
        'link_panel',
    ])
    assert_contains(voucher_service, [
        'def _operation_for_type',
        "return 'expense_create'",
        "return 'expense_edit'",
        "return 'expense_delete'",
        "return 'expense_view'",
        "self._operation_for_type('create', vtype)",
        "self._operation_for_type('edit', vtype)",
        "self._operation_for_type('delete', vtype)",
    ])
    assert_contains(translator, [
        '_PHASE222_EXPENSE_SHELL_TRANSLATIONS',
        'expense_document_subtitle',
        'expense_identity_panel',
        'expense_summary_panel',
        'expense_shell_unified',
    ])
    print('phase222_expense_document_shell_guard passed')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
