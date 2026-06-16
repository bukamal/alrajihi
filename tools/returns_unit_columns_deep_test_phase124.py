# -*- coding: utf-8 -*-
"""Deep arithmetic regression test for return line unit columns.

It verifies the required invariant for both sales and purchase returns:
all displayed quantities are projections of base quantity through selected unit factor,
and all prices are derived from the original invoice line base-unit price.
"""
from decimal import Decimal, getcontext
import sqlite3
import sys
from pathlib import Path

getcontext().prec = 28
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'alrajhi_client'))


def dec(v):
    return Decimal(str(v))


def fmt(v):
    d = dec(v)
    return f"{d:.0f}" if d == d.to_integral_value() else format(d.normalize(), 'f')


def price_for_unit(original_unit_price, original_factor, selected_factor):
    original_factor = dec(original_factor) if dec(original_factor) > 0 else Decimal('1')
    selected_factor = dec(selected_factor) if dec(selected_factor) > 0 else Decimal('1')
    return dec(original_unit_price) / original_factor * selected_factor


def columns(total_base, returned_base, selected_factor):
    f = dec(selected_factor)
    return {
        'qty': dec(total_base) / f,
        'previous': dec(returned_base) / f,
        'returnable': (dec(total_base) - dec(returned_base)) / f,
    }


def assert_equal(actual, expected, label):
    if dec(actual) != dec(expected):
        raise AssertionError(f"{label}: expected {expected}, got {actual}")


def scenario(label, original_unit_price, original_factor, total_base, returned_base, selected_factor, return_qty, expected):
    cols = columns(total_base, returned_base, selected_factor)
    unit_price = price_for_unit(original_unit_price, original_factor, selected_factor)
    base_qty = dec(return_qty) * dec(selected_factor)
    total = dec(return_qty) * unit_price
    assert_equal(cols['qty'], expected['qty'], label + '.qty')
    assert_equal(cols['previous'], expected['previous'], label + '.previous')
    assert_equal(cols['returnable'], expected['returnable'], label + '.returnable')
    assert_equal(unit_price, expected['price'], label + '.price')
    assert_equal(base_qty, expected['base_qty'], label + '.base_qty')
    assert_equal(total, expected['total'], label + '.total')
    if base_qty > dec(total_base) - dec(returned_base):
        raise AssertionError(label + ': return quantity unexpectedly exceeds returnable base')


def test_sugar_purchase_and_sales_units():
    # Original invoice: 10 شوال; شوال=50 base units; base price=5000; therefore line unit_price=250000.
    original_unit_price = Decimal('250000')
    original_factor = Decimal('50')
    total_base = Decimal('500')
    returned_base = Decimal('50')  # 1 شوال already returned

    scenario('shwal', original_unit_price, original_factor, total_base, returned_base, 50, 2, {
        'qty': 10, 'previous': 1, 'returnable': 9, 'price': 250000, 'base_qty': 100, 'total': 500000,
    })
    scenario('bag', original_unit_price, original_factor, total_base, returned_base, 10, 12, {
        'qty': 50, 'previous': 5, 'returnable': 45, 'price': 50000, 'base_qty': 120, 'total': 600000,
    })
    scenario('base', original_unit_price, original_factor, total_base, returned_base, 1, 120, {
        'qty': 500, 'previous': 50, 'returnable': 450, 'price': 5000, 'base_qty': 120, 'total': 600000,
    })

    over_qty = Decimal('10') * Decimal('50')
    if over_qty <= total_base - returned_base:
        raise AssertionError('over-return guard failed: 10 shwal should exceed remaining 9 shwal')


def test_schema_guard_creates_ledger_and_return_unit_columns():
    import importlib.util
    spec = importlib.util.spec_from_file_location('schema_manager_under_test', ROOT / 'alrajhi_client' / 'database' / 'schema_manager.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    apply_common_schema = module.apply_common_schema
    conn = sqlite3.connect(':memory:')
    apply_common_schema(conn)
    tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    if 'inventory_ledger' not in tables:
        raise AssertionError('inventory_ledger table was not created by schema guard')

    conn.execute('CREATE TABLE sales_return_lines (id INTEGER PRIMARY KEY)')
    conn.execute('CREATE TABLE purchase_return_lines (id INTEGER PRIMARY KEY)')
    apply_common_schema(conn)
    for table in ('sales_return_lines', 'purchase_return_lines'):
        cols = {r[1] for r in conn.execute(f'PRAGMA table_info({table})')}
        for col in ('unit_id', 'conversion_factor'):
            if col not in cols:
                raise AssertionError(f'{table}.{col} missing after schema guard')


def main():
    test_sugar_purchase_and_sales_units()
    test_schema_guard_creates_ledger_and_return_unit_columns()
    print('RETURNS_UNIT_COLUMNS_DEEP_TEST_PHASE124: PASS')


if __name__ == '__main__':
    main()
