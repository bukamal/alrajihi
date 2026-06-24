# -*- coding: utf-8 -*-
"""Phase 378 contract: inline runtime hotfix for users, vouchers, cashboxes, and menu routes."""
from __future__ import annotations

import ast
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parents[3]

CHECKS = [
    {
        'target': 'users_document_string_ids',
        'path': 'alrajhi_client/features/users/documents/user_document_tab.py',
        'required': ('self._load_user(user_id)', 'self.document_state.document_id = saved_id', 'self._load_user(saved_id)', 'not widget.isHidden()'),
        'forbidden_text': ('self._load_user(int(user_id))', 'int(saved_id)) if str(saved_id).isdigit()', 'self._load_user(int(saved_id))'),
    },
    {
        'target': 'users_widget_no_modal_fallback',
        'path': 'alrajhi_client/views/widgets/users_widget.py',
        'required': ('open_user_inline', '_selected_user_id', 'UserDocumentTab'),
        'forbidden_text': ('dialog = UserDialog(self)', 'UserDialog(self, user_id=user_id)'),
    },
    {
        'target': 'vouchers_type_specific_inline',
        'path': 'alrajhi_client/views/widgets/vouchers_widget.py',
        'required': ('open_voucher_inline', 'editor.header_panel.set_type(voucher_type)', 'editor.header_panel.type_combo.setEnabled(False)', 'ExpenseDocumentTab'),
        'forbidden_text': (),
    },
    {
        'target': 'cashboxes_master_detail_inline',
        'path': 'alrajhi_client/views/widgets/cashboxes_widget.py',
        'required': ('ResponsiveMasterDetail', 'DetailPlaceholder', 'open_cashbox_inline', 'open_bank_inline', '_close_cashbox_inline_editor', '_close_bank_inline_editor'),
        'forbidden_text': (),
    },
    {
        'target': 'main_menu_inline_routes',
        'path': 'alrajhi_client/views/main_window.py',
        'required': ('_open_page_inline_action', "return self._open_page_inline_action('vouchers', 'open_voucher_inline'", "return self._open_page_inline_action('cashboxes', 'open_cashbox_inline'", "return self._open_page_inline_action('users', 'open_user_inline'"),
        'forbidden_text': (),
    },
    {
        'target': 'manifest_receipt_payment_callbacks',
        'path': 'alrajhi_client/workspace/registry/ui_manifest.py',
        'required': ('callback_key="open_receipt_voucher"', 'callback_key="open_payment_voucher"'),
        'forbidden_text': ('_entry("vouchers_receipt", "receipt_voucher", "hand-holding-usd", page_id="vouchers"', '_entry("vouchers_payment", "payment_voucher", "money-bill-wave", page_id="vouchers"'),
    },
]

FORBIDDEN_CALLS = {
    'alrajhi_client/views/widgets/cashboxes_widget.py': {
        'add_cashbox': ('open_cashbox_document', 'open_document_tab', 'open_tab'),
        'edit_cashbox': ('open_cashbox_document', 'open_document_tab', 'open_tab'),
        'add_bank': ('open_bank_account_document', 'open_document_tab', 'open_tab'),
        'edit_bank': ('open_bank_account_document', 'open_document_tab', 'open_tab'),
    },
    'alrajhi_client/views/main_window.py': {
        'open_category_document': ('_open_document_tab',),
        'open_party_document': ('_open_document_tab',),
        'open_quick_voucher': ('_open_document_tab', 'open_expense_document'),
        'open_branch_document': ('_open_document_tab',),
        'open_warehouse_document': ('_open_document_tab',),
        'open_cashbox_document': ('_open_document_tab',),
        'open_bank_account_document': ('_open_document_tab',),
        'open_inventory_transfer_document': ('_open_document_tab',),
        'open_user_document': ('_open_document_tab',),
    },
}


def _read(path: str, root: Path | None = None) -> str:
    return ((root or ROOT) / path).read_text(encoding='utf-8')


def _calls_in_function(source: str, function_name: str) -> set[str]:
    calls: set[str] = set()
    tree = ast.parse(source)
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


def inline_runtime_hotfix_matrix(root: Path | None = None) -> List[Dict[str, object]]:
    base = root or ROOT
    rows: List[Dict[str, object]] = []
    for spec in CHECKS:
        source = _read(spec['path'], base)
        rows.append({'key': 'parse', 'category': 'source', 'target': spec['target'], 'status': 'pass', 'detail': spec['path'], 'phase': 378})
        for marker in spec.get('required', ()):  # type: ignore[assignment]
            rows.append({'key': f'required:{marker}', 'category': 'required_marker', 'target': spec['target'], 'status': 'pass' if marker in source else 'fail', 'detail': marker, 'phase': 378})
        for marker in spec.get('forbidden_text', ()):  # type: ignore[assignment]
            rows.append({'key': f'forbidden:{marker}', 'category': 'forbidden_text', 'target': spec['target'], 'status': 'pass' if marker not in source else 'fail', 'detail': marker, 'phase': 378})
    for path, functions in FORBIDDEN_CALLS.items():
        source = _read(path, base)
        for fn, forbidden_calls in functions.items():
            calls = _calls_in_function(source, fn)
            for call in forbidden_calls:
                rows.append({'key': f'{fn}:no_{call}', 'category': 'no_sub_tabs', 'target': path, 'status': 'pass' if call not in calls else 'fail', 'detail': ','.join(sorted(calls)), 'phase': 378})
    return rows


def inline_runtime_hotfix_summary(root: Path | None = None) -> Dict[str, object]:
    rows = inline_runtime_hotfix_matrix(root)
    issues = [row for row in rows if row.get('status') != 'pass']
    return {'phase': 378, 'checks': len(rows), 'issues': len(issues), 'issue_groups': len({row.get('category') for row in issues}), 'ready': not issues}


__all__ = ['CHECKS', 'FORBIDDEN_CALLS', 'inline_runtime_hotfix_matrix', 'inline_runtime_hotfix_summary']
