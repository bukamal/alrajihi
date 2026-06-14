# -*- coding: utf-8 -*-
from __future__ import annotations
import ast
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / 'alrajhi_client'
TARGETS = [
    CLIENT / 'views' / 'widgets' / 'pos_widget.py',
    CLIENT / 'views' / 'dialogs' / 'barcode_camera_dialog.py',
]
AR_RE = re.compile(r'[\u0600-\u06FF]')
ALLOW = set()

sys.path.insert(0, str(CLIENT))
from i18n import translate, set_language  # noqa: E402

REQUIRED_KEYS = [
    'pos_fast_title','fullscreen','pos_hint_shortcuts','issue_warehouse','cashbox','no_open_shift',
    'open_shift','close_shift','pos_barcode_placeholder','qty_prefix','camera_scan','item','barcode',
    'unit','quantity','price','total','available','payment_cash','payment_card','payment_credit',
    'payment_method','paid_prefix','change_zero','pos_cash_full_btn','pos_card_btn','pos_suspend_btn',
    'pos_resume_btn','pos_delete_line_btn','pos_clear_cart_btn','pos_checkout_btn','ready_to_scan',
    'cancel_sale','suspend_sale','resume_suspended_sale','print_receipt','barcode_camera_title',
    'start_camera','stop','close','camera_unavailable_msg','barcode_detected'
]

def arabic_literals(path: Path):
    tree = ast.parse(path.read_text(encoding='utf-8'))
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and AR_RE.search(node.value):
            found.append((node.lineno, node.value[:90]))
    return found

def main() -> int:
    errors = []
    for path in TARGETS:
        if not path.exists():
            errors.append(f'missing target: {path}')
            continue
        found = arabic_literals(path)
        if found:
            errors.append(f'{path.relative_to(ROOT)} still has Arabic literals: {found[:20]}')
    for lang in ('ar','de','en'):
        set_language(lang)
        for key in REQUIRED_KEYS:
            value = translate(key, reason='x', value='123', symbology='EAN13', expected='0', id=1, cashbox='Main', amount='0', error='x', item='X', invoice_id=1)
            if value == key:
                errors.append(f'missing translation {lang}:{key}')
    if errors:
        print('\n'.join(errors))
        return 1
    print('OK: POS localization coverage passed')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
