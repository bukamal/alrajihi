# -*- coding: utf-8 -*-
"""Deep regression checks for invoice edit price-change warning.

The GUI cannot be executed in this sandbox because PyQt5 is unavailable.  This
script validates the exact source contract and the money/unit arithmetic that
caused the false warning when editing saved invoices.
"""
from __future__ import annotations
from decimal import Decimal
from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'alrajhi_client' / 'views' / 'dialogs' / 'invoice_dialog.py'
TEXT = SRC.read_text(encoding='utf-8')


def d(value):
    return Decimal(str(value))


def current_unit_price(base_price, factor):
    factor = d(factor)
    if factor <= 0:
        factor = Decimal('1')
    return d(base_price) * factor


def assert_equal(actual, expected, label):
    if d(actual) != d(expected):
        raise AssertionError(f"{label}: expected {expected}, got {actual}")


def assert_true(cond, label):
    if not cond:
        raise AssertionError(label)


def source_order_guard():
    load_idx = TEXT.index('self.lines_model.load_invoice_lines')
    check_idx = TEXT.index('self.check_price_differences(inv)')
    assert_true(load_idx < check_idx, 'price check must run after loading lines into the edit model')


def source_formula_guard():
    assert_true('def _item_current_unit_price_usd' in TEXT, 'missing unit-aware current price helper')
    assert_true('base_price * self._line_conversion_factor(line)' in TEXT, 'current price must be base price multiplied by invoice line conversion factor')
    fn = ast.parse(TEXT)
    check_func = None
    for node in ast.walk(fn):
        if isinstance(node, ast.FunctionDef) and node.name == 'check_price_differences':
            check_func = node
            break
    assert_true(check_func is not None, 'check_price_differences not found')
    check_src = ast.get_source_segment(TEXT, check_func) or ''
    assert_true('_item_current_unit_price_usd' in check_src, 'price warning must use unit-aware helper')
    assert_true("item.get('selling_price' if invoice['type'] == 'sale' else 'purchase_price'" not in check_src,
                'old base-price-only comparison is still present')


def arithmetic_regression_cases():
    # Sale invoice saved as one box. Item master price is stored per base piece.
    assert_equal(current_unit_price('10', '12'), '120', 'sale box unchanged current unit price')
    old_saved = d('120')
    false_old_difference = abs(d('10') - old_saved) > d('0.01')
    fixed_difference = abs(current_unit_price('10', '12') - old_saved) > d('0.01')
    assert_true(false_old_difference, 'control case must reproduce old false warning')
    assert_true(not fixed_difference, 'fixed logic must not warn when only unit factor explains the difference')

    # Real price change: base piece changed from 10 to 11; the displayed new box price must be 132, not 11.
    assert_equal(current_unit_price('11', '12'), '132', 'sale box updated current unit price')
    assert_true(abs(current_unit_price('11', '12') - old_saved) > d('0.01'), 'fixed logic must warn on real master price change')

    # Purchase invoice with decimal factor and decimal purchase price.
    assert_equal(current_unit_price('4.25', '5'), '21.25', 'purchase bundle current unit price')
    assert_true(abs(current_unit_price('4.25', '5') - d('21.25')) <= d('0.01'), 'purchase decimal unit price comparison failed')

    # Invalid/zero factor fallback must not zero prices.
    assert_equal(current_unit_price('9.5', '0'), '9.5', 'zero factor fallback')


def main():
    source_order_guard()
    source_formula_guard()
    arithmetic_regression_cases()
    print('invoice_price_edit_deep_test_phase106: PASS')


if __name__ == '__main__':
    main()
