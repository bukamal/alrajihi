# -*- coding: utf-8 -*-
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding='utf-8')


def test_invoice_routes_enforce_server_branch_scope():
    src = _read('alrajhi_server/repositories/http_route_sql/invoices.py')
    assert 'branch_access_policy.scope_sql' in src
    assert "alias='i'" in src
    assert '_effective_payload_branch(user_id, data)' in src
    assert "context='invoice.update.old'" in src
    assert "context='invoice.delete'" in src
    assert 'BRANCH_ACCESS_DENIED' in src


def test_return_routes_enforce_server_branch_scope():
    src = _read('alrajhi_server/repositories/http_route_sql/returns.py')
    assert '_branch_where(user_id, \'sr\'' in src
    assert '_branch_where(user_id, \'pr\'' in src
    assert "sales_return.invoice_lines" in src
    assert "purchase_return.invoice_lines" in src
    assert "sales_return.delete" in src
    assert "purchase_return.delete" in src
    assert 'BRANCH_ACCESS_DENIED' in src


def test_warehouse_cashbox_routes_enforce_server_branch_scope():
    wh = _read('alrajhi_server/repositories/http_route_sql/warehouses.py')
    cb = _read('alrajhi_server/repositories/http_route_sql/cashboxes.py')
    assert '_require_warehouse_access' in wh
    assert "warehouse_transfer.from" in wh
    assert "warehouse_transfer.to" in wh
    assert "alias='w'" in wh
    assert "cashbox.update.old" in cb
    assert "cashbox.delete" in cb
    assert "alias='c'" in cb
    assert "alias='ba'" in cb


def test_reports_have_branch_scoped_summary_and_income_statement():
    src = _read('alrajhi_server/repositories/http_route_sql/reports.py')
    assert 'def _report_branch_scope' in src
    assert 'invoice_branch_sql' in src
    assert 'voucher_branch_sql' in src
    assert 'sales_return_branch_sql' in src
    assert 'purchase_return_branch_sql' in src


def test_branch_scoped_sql_helper_exports_canonical_scopes():
    src = _read('alrajhi_server/services/branch_scoped_sql.py')
    for name in ('invoice_scope', 'return_scope', 'warehouse_scope', 'cashbox_scope'):
        assert f'def {name}' in src
    assert 'branch_access_policy.scope_sql' in src
