# -*- coding: utf-8 -*-
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding='utf-8')


def test_restaurant_branch_scope_helper_exists_and_uses_canonical_policy():
    src = _read('alrajhi_server/services/restaurant_branch_scope.py')
    assert 'def restaurant_branch_guard' in src
    assert 'def filter_restaurant_records' in src
    assert 'def scope_creation_payload' in src
    assert 'branch_access_policy.effective_branch_id' in src
    assert 'BRANCH_ACCESS_DENIED' in src
    for lookup in ('session_branch', 'table_branch', 'line_branch', 'ticket_branch', 'split_bill_branch', 'print_job_branch'):
        assert f'def {lookup}' in src


def test_restaurant_routes_are_guarded_and_lists_are_filtered():
    src = _read('alrajhi_server/services/http_routes/restaurant.py')
    assert 'restaurant_branch_guard' in src
    assert 'filter_restaurant_records(get_jwt_identity(), _repo.list_tables' in src
    assert 'filter_restaurant_records(get_jwt_identity(), _repo.list_kitchen_tickets' in src
    assert 'filter_restaurant_records(get_jwt_identity(), _repo.list_restaurant_orders' in src
    assert '@restaurant_branch_guard(create=True)' in src
    assert 'scope_creation_payload(get_jwt_identity(), context="restaurant_takeaway_order")' in src
    assert 'scope_creation_payload(get_jwt_identity(), context="restaurant_delivery_order")' in src


def test_restaurant_repository_is_branch_aware_for_sessions_tickets_and_checkout():
    src = _read('alrajhi_server/repositories/restaurant_repository.py')
    for column in (
        'restaurant_tables ADD COLUMN branch_id',
        'restaurant_sessions ADD COLUMN branch_id',
        'kitchen_tickets ADD COLUMN branch_id',
        'restaurant_payments ADD COLUMN branch_id',
        'restaurant_reservations ADD COLUMN branch_id',
    ):
        assert column in src
    assert 'def open_table(self, table_id: int, waiter_id: str | None = None, guests: int = 1, notes: str = "", branch_id: int | None = None)' in src
    assert 'COALESCE(s.branch_id, t.branch_id) AS branch_id' in src
    assert 'INSERT INTO kitchen_tickets(session_id, station_id, branch_id' in src
    assert 'INSERT INTO invoices (user_id, type, date, reference, notes, total, paid, status, workflow_status, original_currency, payment_method, branch_id)' in src
    assert "session.get('branch_id')" in src


def test_branch_scoped_sql_exports_restaurant_scope():
    src = _read('alrajhi_server/services/branch_scoped_sql.py')
    assert 'def restaurant_scope' in src
    assert "branch_column='branch_id'" in src
    assert "'restaurant_scope'" in src
