# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'tools' / 'audit_outputs' / 'voucher_master_detail_inline_matrix.csv'
VOUCHERS = ROOT / 'alrajhi_client' / 'views' / 'widgets' / 'vouchers_widget.py'
CUSTOMERS = ROOT / 'alrajhi_client' / 'views' / 'widgets' / 'customers_widget.py'
SUPPLIERS = ROOT / 'alrajhi_client' / 'views' / 'widgets' / 'suppliers_widget.py'

REQUIRED_MARKERS = [
    'ResponsiveMasterDetail',
    'DetailPlaceholder',
    'detail_panel',
    'detail_stack',
    'inline_editor_page',
    'inline_editor_host',
    '_connect_selection_preview',
    '_update_detail_preview',
    '_show_inline_voucher_editor',
    'self.master_detail = ResponsiveMasterDetail(self.table, self.detail_stack, self)',
]

FORBIDDEN_TOP_LEVEL_STACK_MARKERS = [
    'self.stack = QStackedWidget',
    'self.list_page = QWidget',
    'self.stack.addWidget(self.list_page)',
    'self.stack.setCurrentWidget(self.editor_page)',
]

FORBIDDEN_FUNCTION_CALLS = {
    'add_voucher': {'open_quick_voucher', 'open_document_tab', 'open_tab'},
    'edit_voucher': {'open_quick_voucher', 'open_document_tab', 'open_tab'},
}


def _calls_in_function(tree: ast.AST, function_name: str) -> set[str]:
    calls: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == function_name:
            for sub in ast.walk(node):
                if isinstance(sub, ast.Call):
                    func = sub.func
                    if isinstance(func, ast.Attribute):
                        calls.add(func.attr)
                    elif isinstance(func, ast.Name):
                        calls.add(func.id)
    return calls


def main() -> int:
    rows: list[dict[str, str]] = []
    issues: list[str] = []
    source = VOUCHERS.read_text(encoding='utf-8')
    tree = ast.parse(source)
    rows.append({'target': 'vouchers', 'check': 'parse', 'status': 'ok', 'detail': str(VOUCHERS.relative_to(ROOT))})

    for marker in REQUIRED_MARKERS:
        ok = marker in source
        rows.append({'target': 'vouchers', 'check': f'marker:{marker}', 'status': 'ok' if ok else 'fail', 'detail': marker})
        if not ok:
            issues.append(f'vouchers missing {marker}')

    for marker in FORBIDDEN_TOP_LEVEL_STACK_MARKERS:
        ok = marker not in source
        rows.append({'target': 'vouchers', 'check': f'no_legacy_full_page_stack:{marker}', 'status': 'ok' if ok else 'fail', 'detail': marker})
        if not ok:
            issues.append(f'vouchers still use full-page stack marker {marker}')

    for fn, forbidden_calls in FORBIDDEN_FUNCTION_CALLS.items():
        calls = _calls_in_function(tree, fn)
        for call in forbidden_calls:
            ok = call not in calls
            rows.append({'target': 'vouchers', 'check': f'{fn}:no_{call}', 'status': 'ok' if ok else 'fail', 'detail': ','.join(sorted(calls))})
            if not ok:
                issues.append(f'{fn} still calls {call}')

    for voucher_type in ('receipt', 'payment', 'expense'):
        ok = f"add_voucher('{voucher_type}')" in source and f"'{voucher_type}'" in source
        rows.append({'target': 'vouchers', 'check': f'inline_type:{voucher_type}', 'status': 'ok' if ok else 'fail', 'detail': voucher_type})
        if not ok:
            issues.append(f'missing inline voucher type {voucher_type}')

    # Phase379: customers/suppliers delegate the shared structure to
    # PartyInlineEditorHostMixin instead of duplicating the QStackedWidget and
    # ResponsiveMasterDetail boilerplate in each list file.
    for name, path in [('customers', CUSTOMERS), ('suppliers', SUPPLIERS)]:
        text = path.read_text(encoding='utf-8')
        for marker in ('PartyInlineEditorHostMixin', '_install_party_inline_host'):
            ok = marker in text and marker in source or marker in text
            rows.append({'target': name, 'check': f'shared_structure:{marker}', 'status': 'ok' if ok else 'fail', 'detail': marker})
            if not ok:
                issues.append(f'{name} missing shared party inline structure marker: {marker}')

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open('w', encoding='utf-8', newline='') as fh:
        writer = csv.DictWriter(fh, fieldnames=['target', 'check', 'status', 'detail'])
        writer.writeheader()
        writer.writerows(rows)

    if issues:
        for issue in issues:
            print('FAIL:', issue)
        return 1
    print(f'Phase376 voucher master-detail inline guard passed: {len(rows)} checks / 0 issues')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
