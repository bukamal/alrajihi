#!/usr/bin/env python3
from __future__ import annotations

import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding='utf-8')

def assert_contains(rel: str, needle: str) -> None:
    text = read(rel)
    if needle not in text:
        raise AssertionError(f'{rel} missing required snippet: {needle}')

def main() -> None:
    # POS does not edit material names in-grid; it must use barcode_input_service.
    assert_contains('alrajhi_client/core/services/pos_service.py', 'barcode_input_service.lookup_entry')
    assert_contains('alrajhi_client/features/pos/pos_line_schema.py', 'TransactionColumn("item", "transaction_column_item", True, True, True, 280, True, editable=False)')
    assert_contains('alrajhi_client/features/pos/pos_line_model.py', 'return Qt.ItemIsEnabled | Qt.ItemIsSelectable')

    # Returns material cells are readonly because they are derived from the original invoice.
    schema = read('alrajhi_client/features/transactions/grids/transaction_column_schema.py')
    if 'def sales_return_schema' not in schema or 'def purchase_return_schema' not in schema:
        raise AssertionError('Return schemas not found')
    for marker in (
        'TransactionColumn("item", "transaction_column_item", True, True, True, 260, True, editable=False)',
    ):
        if schema.count(marker) < 2:
            raise AssertionError('Return item columns must remain read-only in both sales/purchase return schemas')

    # Shared grid must not attach material/unit editors to read-only item/unit columns.
    grid = read('alrajhi_client/features/transactions/grids/transaction_line_grid.py')
    for needle in (
        'getattr(item_column, "editable", True)',
        'getattr(unit_column, "editable", True)',
        'TransactionItemDelegate',
        'TransactionUnitDelegate',
    ):
        if needle not in grid:
            raise AssertionError(f'TransactionLineGrid delegate guard missing {needle}')

    # Restaurant menu lookup should be explicitly case-insensitive on local and server sides.
    for rel in (
        'alrajhi_client/gateways/local/restaurant_gateway.py',
        'alrajhi_server/repositories/restaurant_repository.py',
    ):
        txt = read(rel)
        if "LOWER(COALESCE(name, '')) LIKE LOWER(?)" not in txt or "LOWER(COALESCE(barcode, '')) LIKE LOWER(?)" not in txt:
            raise AssertionError(f'{rel} restaurant menu search is not explicitly case-insensitive')

    # SQL behavior regression test with case_sensitive_like enabled.
    conn = sqlite3.connect(':memory:')
    conn.execute('PRAGMA case_sensitive_like=ON')
    conn.execute('CREATE TABLE items(id INTEGER PRIMARY KEY, name TEXT, barcode TEXT, deleted_at TEXT)')
    conn.execute('INSERT INTO items(name, barcode, deleted_at) VALUES (?, ?, ?)', ('Milk Box', 'AbC123', ''))
    term = '%milk%'
    row = conn.execute("SELECT id FROM items WHERE COALESCE(deleted_at, '') = '' AND (LOWER(COALESCE(name, '')) LIKE LOWER(?) OR LOWER(COALESCE(barcode, '')) LIKE LOWER(?))", (term, term)).fetchone()
    if not row:
        raise AssertionError('Explicit case-insensitive restaurant search failed under case_sensitive_like=ON')
    term = '%abc%'
    row = conn.execute("SELECT id FROM items WHERE COALESCE(deleted_at, '') = '' AND (LOWER(COALESCE(name, '')) LIKE LOWER(?) OR LOWER(COALESCE(barcode, '')) LIKE LOWER(?))", (term, term)).fetchone()
    if not row:
        raise AssertionError('Explicit case-insensitive barcode search failed under case_sensitive_like=ON')

    print('phase186_pos_returns_lookup_audit_guard passed')

if __name__ == '__main__':
    main()
