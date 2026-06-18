#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Guard Phase 50 party document tabs.

Customers and suppliers must open as workspace document tabs, not modal-only add/edit flows.
The tab keeps CRUD behind EntityService and exposes statement/invoices/vouchers panels for
later account-statement integration.
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PARTY_TAB = ROOT / 'alrajhi_client' / 'features' / 'parties' / 'party_editor_tab.py'
MAIN = ROOT / 'alrajhi_client' / 'views' / 'main_window.py'
CUSTOMERS = ROOT / 'alrajhi_client' / 'views' / 'widgets' / 'customers_widget.py'
SUPPLIERS = ROOT / 'alrajhi_client' / 'views' / 'widgets' / 'suppliers_widget.py'


def main() -> int:
    errors: list[str] = []
    for path in (PARTY_TAB, MAIN, CUSTOMERS, SUPPLIERS):
        if not path.exists():
            errors.append(f'missing {path.relative_to(ROOT)}')
            continue
        try:
            ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
        except SyntaxError as exc:
            errors.append(f'syntax error in {path.relative_to(ROOT)}:{exc.lineno}: {exc.msg}')

    text = PARTY_TAB.read_text(encoding='utf-8') if PARTY_TAB.exists() else ''
    required_party_tokens = [
        'class PartyEditorTab(BaseDocumentTab)',
        'entity_service.add_customer',
        'entity_service.update_customer',
        'entity_service.add_supplier',
        'entity_service.update_supplier',
        'voucher_service.list_vouchers',
        'reporting_service.customer_statement',
        'invoice_service.list_records',
        'self.tabs.addTab(self.statement_table',
        'self.tabs.addTab(self.invoices_table',
        'self.tabs.addTab(self.vouchers_table',
    ]
    for token in required_party_tokens:
        if token not in text:
            errors.append(f'PartyEditorTab missing token: {token}')

    main_text = MAIN.read_text(encoding='utf-8') if MAIN.exists() else ''
    for token in ('def open_party_document', 'from features.parties import PartyEditorTab', "open_party_document('customer')", "open_party_document('supplier')"):
        if token not in main_text:
            errors.append(f'main_window missing party document integration: {token}')

    customers_text = CUSTOMERS.read_text(encoding='utf-8') if CUSTOMERS.exists() else ''
    suppliers_text = SUPPLIERS.read_text(encoding='utf-8') if SUPPLIERS.exists() else ''
    if "main.open_party_document('customer'" not in customers_text:
        errors.append('CustomersWidget add/edit does not route to customer document tabs')
    if "main.open_party_document('supplier'" not in suppliers_text:
        errors.append('SuppliersWidget add/edit does not route to supplier document tabs')

    if errors:
        print('Phase 50 party document tabs guard failed:')
        for error in errors:
            print(f' - {error}')
        return 1
    print('Phase 50 party document tabs guard passed.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
