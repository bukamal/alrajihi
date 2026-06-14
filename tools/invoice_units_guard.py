#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Static guard for invoice item names and sub-unit pricing.

Prevents regressions where:
- loaded invoice lines lose item_name because API/DB uses a different key;
- changing unit updates the unit column instead of the price column;
- conversion factors stay as strings and break totals.
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
invoice_dialog = ROOT / 'alrajhi_client' / 'views' / 'dialogs' / 'invoice_dialog.py'
delegates = ROOT / 'alrajhi_client' / 'views' / 'dialogs' / 'invoice_delegates.py'

text = invoice_dialog.read_text(encoding='utf-8')
del_text = delegates.read_text(encoding='utf-8')

checks = {
    'item name fallback includes product_name/name/item fallback': "val(line, 'product_name')" in text and "(item or {}).get('name'" in text,
    'invoice payload includes item_name': "'item_name': line.get('item_name', '')" in text and "'item_name': line.get('item_name', '')," in text,
    'conversion factor normalized on unit set': "line['conversion_factor'] = _positive_decimal(value[2]" in text,
    'delegate uses COL_PRICE not hardcoded unit column': "price_col = getattr(model, 'COL_PRICE', 5)" in del_text,
    'delegate normalizes old/new factors': "old_factor = _positive_decimal" in del_text and "new_factor = _positive_decimal" in del_text,
}
failed = [name for name, ok in checks.items() if not ok]
if failed:
    print('invoice_units_guard FAILED:')
    for name in failed:
        print(' -', name)
    sys.exit(1)
print('invoice_units_guard: PASS')
