# -*- coding: utf-8 -*-
"""Phase 381 contract: document editors use canonical layout families."""
from __future__ import annotations

import ast
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parents[3]
PHASE = 381

FILES = {
    'layout_policy': 'alrajhi_client/workspace/documents/document_layout_policy.py',
    'base_document_tab': 'alrajhi_client/workspace/documents/base_document_tab.py',
    'documents_init': 'alrajhi_client/workspace/documents/__init__.py',
    'unified_inline_workspace': 'alrajhi_client/views/widgets/unified_inline_workspace.py',
    'transaction_layout': 'alrajhi_client/features/transactions/components/transaction_document_layout.py',
}

REQUIRED_MARKERS = {
    'layout_policy': (
        'KIND_CARD_FORM = "card_form"',
        'KIND_FINANCIAL_DOCUMENT = "financial_document"',
        'KIND_TABULAR_DOCUMENT = "tabular_document"',
        'CARD_FORM_TYPES',
        'FINANCIAL_DOCUMENT_TYPES',
        'TABULAR_DOCUMENT_TYPES',
        'infer_document_layout_kind',
        'apply_document_layout_policy',
        '_hide_duplicate_inline_headers',
        '_configure_card_form',
        '_configure_financial_document',
        '_configure_tabular_document',
        'documentLayoutKind',
        'documentInlineMode',
        'documentLayoutManaged',
        'HEADER_OBJECT_NAMES',
    ),
    'base_document_tab': (
        'from .document_layout_policy import apply_document_layout_policy',
        'def apply_document_layout_profile',
        'self.apply_document_layout_profile()',
    ),
    'documents_init': (
        'KIND_CARD_FORM',
        'KIND_FINANCIAL_DOCUMENT',
        'KIND_TABULAR_DOCUMENT',
        'apply_document_layout_policy',
        'infer_document_layout_kind',
    ),
    'unified_inline_workspace': (
        'from workspace.documents.document_layout_policy import apply_document_layout_policy',
        'editor.setProperty(\'inlineEditor\', True)',
        'editor.apply_document_layout_profile(inline=True)',
        'apply_document_layout_policy(editor, inline=True)',
        'Phase381',
    ),
    'transaction_layout': (
        'TransactionDocumentLayout',
        'TransactionDocumentSplitter',
        'TransactionLineGrid',
        'setStretchFactor(0, 7)',
        'setStretchFactor(1, 2)',
    ),
}

EXPECTED_TYPE_MARKERS = {
    'card_form': ('customer', 'supplier', 'user', 'category', 'warehouse', 'branch', 'cashbox', 'bank_account', 'material'),
    'financial_document': ('voucher', 'expense'),
    'tabular_document': ('sales_invoice', 'purchase_invoice', 'sales_return', 'purchase_return', 'warehouse_transfer', 'bom', 'production_order'),
}

FORBIDDEN_MARKERS = {
    'unified_inline_workspace': (
        '# Remove duplicate header/title rows from simple card editors when they',
    ),
}


def _read(path: str, root: Path | None = None) -> str:
    return ((root or ROOT) / path).read_text(encoding='utf-8')


def document_layout_family_matrix(root: Path | None = None) -> List[Dict[str, object]]:
    base = root or ROOT
    rows: List[Dict[str, object]] = []
    for key, path in FILES.items():
        source = _read(path, base)
        ast.parse(source)
        rows.append({'key': 'parse', 'category': 'source', 'target': key, 'status': 'pass', 'detail': path, 'phase': PHASE})
        for marker in REQUIRED_MARKERS.get(key, ()):  # type: ignore[arg-type]
            rows.append({'key': f'required:{marker}', 'category': 'required_marker', 'target': key, 'status': 'pass' if marker in source else 'fail', 'detail': marker, 'phase': PHASE})
        for marker in FORBIDDEN_MARKERS.get(key, ()):  # type: ignore[arg-type]
            rows.append({'key': f'forbidden:{marker}', 'category': 'forbidden_marker', 'target': key, 'status': 'pass' if marker not in source else 'fail', 'detail': marker, 'phase': PHASE})
    policy_source = _read(FILES['layout_policy'], base)
    for family, markers in EXPECTED_TYPE_MARKERS.items():
        for marker in markers:
            rows.append({'key': f'{family}:{marker}', 'category': 'type_family', 'target': family, 'status': 'pass' if f'"{marker}"' in policy_source else 'fail', 'detail': marker, 'phase': PHASE})
    return rows


def document_layout_family_summary(root: Path | None = None) -> Dict[str, object]:
    rows = document_layout_family_matrix(root)
    issues = [row for row in rows if row.get('status') != 'pass']
    return {'phase': PHASE, 'checks': len(rows), 'issues': len(issues), 'issue_groups': len({row.get('category') for row in issues}), 'ready': not issues}


__all__ = [
    'FILES',
    'REQUIRED_MARKERS',
    'EXPECTED_TYPE_MARKERS',
    'FORBIDDEN_MARKERS',
    'document_layout_family_matrix',
    'document_layout_family_summary',
]
