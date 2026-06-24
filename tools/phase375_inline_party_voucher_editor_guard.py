# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'tools' / 'audit_outputs' / 'inline_party_voucher_editor_matrix.csv'

TARGETS = {
    'customers': ROOT / 'alrajhi_client' / 'views' / 'widgets' / 'customers_widget.py',
    'suppliers': ROOT / 'alrajhi_client' / 'views' / 'widgets' / 'suppliers_widget.py',
    'vouchers': ROOT / 'alrajhi_client' / 'views' / 'widgets' / 'vouchers_widget.py',
}

REQUIRED_MARKERS = {
    'customers': ['QStackedWidget', 'detail_stack', '_show_inline_party_editor', 'PartyEditorTab', '_after_inline_party_saved'],
    'suppliers': ['QStackedWidget', 'detail_stack', '_show_inline_party_editor', 'PartyEditorTab', '_after_inline_party_saved'],
    'vouchers': ['QStackedWidget', 'add_receipt_action', 'add_payment_action', 'add_expense_action', '_show_inline_voucher_editor', 'VoucherEditorTab', 'ExpenseDocumentTab'],
}

FORBIDDEN_CALLS = {
    'customers': {'add_customer': ['open_party_document'], 'edit_customer': ['open_party_document']},
    'suppliers': {'add_supplier': ['open_party_document'], 'edit_supplier': ['open_party_document']},
    'vouchers': {'add_voucher': ['open_quick_voucher'], 'edit_voucher': ['open_quick_voucher']},
}


def _function_calls(tree: ast.AST, name: str) -> list[str]:
    calls: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            for sub in ast.walk(node):
                if isinstance(sub, ast.Call):
                    func = sub.func
                    if isinstance(func, ast.Attribute):
                        calls.append(func.attr)
                    elif isinstance(func, ast.Name):
                        calls.append(func.id)
    return calls


def main() -> int:
    rows = []
    issues = []
    for key, path in TARGETS.items():
        source = path.read_text(encoding='utf-8')
        rows.append({'target': key, 'check': 'parse', 'status': 'ok', 'detail': str(path.relative_to(ROOT))})
        tree = ast.parse(source)
        for marker in REQUIRED_MARKERS[key]:
            ok = marker in source
            rows.append({'target': key, 'check': f'marker:{marker}', 'status': 'ok' if ok else 'fail', 'detail': marker})
            if not ok:
                issues.append(f'{key} missing {marker}')
        for fn, forbidden in FORBIDDEN_CALLS[key].items():
            calls = _function_calls(tree, fn)
            for call in forbidden:
                ok = call not in calls
                rows.append({'target': key, 'check': f'{fn}:no_{call}', 'status': 'ok' if ok else 'fail', 'detail': ','.join(calls)})
                if not ok:
                    issues.append(f'{key}.{fn} still calls {call}')
        if key == 'vouchers':
            for voucher_type in ('receipt', 'payment', 'expense'):
                ok = f"add_voucher('{voucher_type}')" in source or f"voucher_type='{voucher_type}'" in source or f"'{voucher_type}'" in source
                rows.append({'target': key, 'check': f'inline_type:{voucher_type}', 'status': 'ok' if ok else 'fail', 'detail': voucher_type})
                if not ok:
                    issues.append(f'voucher inline type missing {voucher_type}')
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open('w', encoding='utf-8', newline='') as fh:
        writer = csv.DictWriter(fh, fieldnames=['target', 'check', 'status', 'detail'])
        writer.writeheader()
        writer.writerows(rows)
    if issues:
        for issue in issues:
            print('FAIL:', issue)
        return 1
    print(f'Phase375 inline party/voucher editor guard passed: {len(rows)} checks / 0 issues')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
