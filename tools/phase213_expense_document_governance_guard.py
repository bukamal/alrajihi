# -*- coding: utf-8 -*-
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def read(rel):
    return (ROOT / rel).read_text(encoding='utf-8')

def require(cond, msg):
    if not cond:
        raise AssertionError(msg)

def main():
    policy = read('alrajhi_client/core/services/finance_operation_policy.py')
    for token in ['OP_EXPENSE_CREATE', 'OP_EXPENSE_EDIT', 'OP_EXPENSE_DELETE', 'OP_EXPENSE_PRINT', 'OP_EXPENSE_VIEW']:
        require(token in policy, f'missing {token}')
    require('allow_expense_create' in read('alrajhi_client/core/services/settings_service.py'), 'finance settings missing expense switches')
    perms = read('alrajhi_client/core/services/permission_service.py')
    for token in ['ACTION_EXPENSE_CREATE', 'finance.expense.create', 'finance.expense.print']:
        require(token in perms, f'permission service missing {token}')
    rbac = read('alrajhi_client/core/services/rbac_service.py')
    require('finance_expense_create' in rbac and 'finance.expense.create' in rbac, 'RBAC missing expense permission map/defaults')
    exp = read('alrajhi_client/features/finance/documents/expense_document_tab.py')
    require('class ExpenseDocumentTab' in exp, 'ExpenseDocumentTab missing')
    require("data['type'] = 'expense'" in exp, 'ExpenseDocumentTab must force type expense')
    require('OP_EXPENSE_PRINT' in exp and 'OP_EXPENSE_CREATE' in exp, 'ExpenseDocumentTab must enforce expense-specific policy')
    mainw = read('alrajhi_client/views/main_window.py')
    require('def open_expense_document' in mainw, 'MainWindow missing open_expense_document')
    require("voucher_type == 'expense'" in mainw, 'quick voucher expense not routed')
    service = read('alrajhi_client/core/services/expense_service.py')
    for token in ["'expense_view'", "'expense_create'", "'expense_delete'"]:
        require(token in service, f'ExpenseService missing governance {token}')
    mig = read('alrajhi_client/database/migrations.py')
    require('finance.expense.create' in mig and 'finance.expense.print' in mig, 'client migrations missing expense permissions')
    server_mig = read('alrajhi_server/database/migrations.py')
    require('finance.expense.create' in server_mig and 'finance.expense.print' in server_mig, 'server migrations missing expense permissions')
    print('phase213_expense_document_governance_guard: OK')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
