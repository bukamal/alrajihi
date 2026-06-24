# -*- coding: utf-8 -*-
"""Phase379 contract: unified wide inline layout for party editors."""
from __future__ import annotations

import ast
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parents[3]

CHECKS = [
    {
        'target': 'shared_party_inline_host',
        'path': 'alrajhi_client/views/widgets/party_inline_editor_host.py',
        'required': (
            'class PartyInlineEditorHostMixin',
            '_install_unified_inline_workspace',
            'master_weight=2',
            'detail_weight=3',
            'inline_mode=True',
            '_show_inline_party_editor',
            '_after_inline_party_saved',
        ),
        'forbidden_text': ('inline_title_label', 'InlineEditorTitle'),
    },
    {
        'target': 'customer_inline_uses_shared_host',
        'path': 'alrajhi_client/views/widgets/customers_widget.py',
        'required': (
            'PartyInlineEditorHostMixin',
            '_install_party_inline_host',
            "_show_inline_party_editor('customer'",
        ),
        'forbidden_text': ('inline_title_label', 'InlineEditorTitle', 'DocumentHeaderCard'),
    },
    {
        'target': 'supplier_inline_uses_shared_host',
        'path': 'alrajhi_client/views/widgets/suppliers_widget.py',
        'required': (
            'PartyInlineEditorHostMixin',
            '_install_party_inline_host',
            "_show_inline_party_editor('supplier'",
        ),
        'forbidden_text': ('inline_title_label', 'InlineEditorTitle', 'DocumentHeaderCard'),
    },
    {
        'target': 'party_editor_inline_hides_document_header',
        'path': 'alrajhi_client/features/parties/party_editor_tab.py',
        'required': (
            'inline_mode: bool = False',
            'self.inline_mode = bool(inline_mode)',
            'if not self.inline_mode:',
            'root.addWidget(self._build_header())',
        ),
        'forbidden_text': (),
    },
]

FORBIDDEN_CALLS = {
    'alrajhi_client/views/widgets/customers_widget.py': {
        'add_customer': ('open_party_document', 'open_document_tab', 'open_tab'),
        'edit_customer': ('open_party_document', 'open_document_tab', 'open_tab'),
    },
    'alrajhi_client/views/widgets/suppliers_widget.py': {
        'add_supplier': ('open_party_document', 'open_document_tab', 'open_tab'),
        'edit_supplier': ('open_party_document', 'open_document_tab', 'open_tab'),
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


def inline_party_layout_unification_matrix(root: Path | None = None) -> List[Dict[str, object]]:
    base = root or ROOT
    rows: List[Dict[str, object]] = []
    for spec in CHECKS:
        source = _read(spec['path'], base)
        ast.parse(source)
        rows.append({'key': 'parse', 'category': 'source', 'target': spec['target'], 'status': 'pass', 'detail': spec['path'], 'phase': 379})
        for marker in spec.get('required', ()):  # type: ignore[assignment]
            rows.append({'key': f'required:{marker}', 'category': 'required_marker', 'target': spec['target'], 'status': 'pass' if marker in source else 'fail', 'detail': marker, 'phase': 379})
        for marker in spec.get('forbidden_text', ()):  # type: ignore[assignment]
            rows.append({'key': f'forbidden:{marker}', 'category': 'forbidden_text', 'target': spec['target'], 'status': 'pass' if marker not in source else 'fail', 'detail': marker, 'phase': 379})
    for path, funcs in FORBIDDEN_CALLS.items():
        source = _read(path, base)
        for fn, forbidden in funcs.items():
            calls = _calls_in_function(source, fn)
            for call in forbidden:
                rows.append({'key': f'{fn}:no_{call}', 'category': 'no_sub_tabs', 'target': path, 'status': 'pass' if call not in calls else 'fail', 'detail': ','.join(sorted(calls)), 'phase': 379})
    return rows


def inline_party_layout_unification_summary(root: Path | None = None) -> Dict[str, object]:
    rows = inline_party_layout_unification_matrix(root)
    issues = [row for row in rows if row.get('status') != 'pass']
    return {'phase': 379, 'checks': len(rows), 'issues': len(issues), 'issue_groups': len({row.get('category') for row in issues}), 'ready': not issues}


__all__ = ['CHECKS', 'FORBIDDEN_CALLS', 'inline_party_layout_unification_matrix', 'inline_party_layout_unification_summary']
