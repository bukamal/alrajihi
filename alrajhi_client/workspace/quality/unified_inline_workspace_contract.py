# -*- coding: utf-8 -*-
"""Phase 380 contract: one unified inline workspace shell for list/detail editors."""
from __future__ import annotations

import ast
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parents[3]
PHASE = 380

FILES = {
    'unified_host': 'alrajhi_client/views/widgets/unified_inline_workspace.py',
    'inline_document_host': 'alrajhi_client/views/widgets/inline_document_host.py',
    'party_inline_host': 'alrajhi_client/views/widgets/party_inline_editor_host.py',
    'vouchers': 'alrajhi_client/views/widgets/vouchers_widget.py',
    'cashboxes': 'alrajhi_client/views/widgets/cashboxes_widget.py',
    'responsive_master_detail': 'alrajhi_client/ui/components/responsive_master_detail.py',
}

REQUIRED_MARKERS = {
    'unified_host': (
        'class UnifiedInlineWorkspaceMixin',
        '_install_unified_inline_workspace',
        '_show_unified_inline_editor',
        '_close_unified_inline_editor',
        '_wire_unified_inline_close',
        '_apply_unified_inline_visual_policy',
        'UnifiedInlineEditorPage',
        'UnifiedInlineEditorHost',
        'UnifiedInlineBackButton',
        'master_weight: int = 2',
        'detail_weight: int = 3',
    ),
    'inline_document_host': (
        'class InlineDocumentHostMixin(UnifiedInlineWorkspaceMixin)',
        '_install_unified_inline_workspace',
        '_show_unified_inline_editor',
        '_wire_unified_inline_close',
        'master_weight=2',
        'detail_weight=3',
    ),
    'party_inline_host': (
        'class PartyInlineEditorHostMixin(UnifiedInlineWorkspaceMixin)',
        '_install_unified_inline_workspace',
        '_show_unified_inline_editor',
        'inline_mode=True',
        'master_weight=2',
        'detail_weight=3',
    ),
    'vouchers': (
        'class VouchersWidget(UnifiedInlineWorkspaceMixin, QWidget)',
        '_install_unified_inline_workspace',
        '_show_unified_inline_editor',
        'VoucherEditorTab',
        'ExpenseDocumentTab',
    ),
    'cashboxes': (
        'ResponsiveMasterDetail(self.cash_table, self.cash_detail_stack, self.cash_tab, master_weight=2, detail_weight=3)',
        'ResponsiveMasterDetail(self.bank_table, self.bank_detail_stack, self.bank_tab, master_weight=2, detail_weight=3)',
        'UnifiedInlineBackButton',
        'UnifiedInlineHiddenTitle',
    ),
    'responsive_master_detail': (
        'self.master_weight',
        'self.detail_weight',
        'master_width = int(total_width * self.master_weight / total_weight)',
        'self.splitter.setSizes([master_width, detail_width])',
    ),
}

FORBIDDEN_MARKERS = {
    'inline_document_host': ('InlineEditorTitle', 'inline_title_label'),
    'party_inline_host': ('InlineEditorTitle', 'inline_title_label'),
    'vouchers': ('InlineEditorTitle', 'inline_title_label'),
    'cashboxes': ('InlineEditorTitle',),
}

NO_DIRECT_SUBTAB_FUNCTIONS = {
    'vouchers': {
        'add_voucher': ('open_quick_voucher', 'open_document_tab', 'open_tab'),
        'edit_voucher': ('open_quick_voucher', 'open_document_tab', 'open_tab'),
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


def unified_inline_workspace_matrix(root: Path | None = None) -> List[Dict[str, object]]:
    base = root or ROOT
    rows: List[Dict[str, object]] = []
    for key, path in FILES.items():
        source = _read(path, base)
        ast.parse(source)
        rows.append({'key': 'parse', 'category': 'source', 'target': key, 'status': 'pass', 'detail': path, 'phase': PHASE})
        for marker in REQUIRED_MARKERS.get(key, ()):
            rows.append({'key': f'required:{marker}', 'category': 'required_marker', 'target': key, 'status': 'pass' if marker in source else 'fail', 'detail': marker, 'phase': PHASE})
        for marker in FORBIDDEN_MARKERS.get(key, ()):
            rows.append({'key': f'forbidden:{marker}', 'category': 'forbidden_marker', 'target': key, 'status': 'pass' if marker not in source else 'fail', 'detail': marker, 'phase': PHASE})
    for key, functions in NO_DIRECT_SUBTAB_FUNCTIONS.items():
        source = _read(FILES[key], base)
        for fn, forbidden in functions.items():
            calls = _calls_in_function(source, fn)
            for call in forbidden:
                rows.append({'key': f'{fn}:no_{call}', 'category': 'no_sub_tabs', 'target': key, 'status': 'pass' if call not in calls else 'fail', 'detail': ','.join(sorted(calls)), 'phase': PHASE})
    return rows


def unified_inline_workspace_summary(root: Path | None = None) -> Dict[str, object]:
    rows = unified_inline_workspace_matrix(root)
    issues = [row for row in rows if row.get('status') != 'pass']
    return {'phase': PHASE, 'checks': len(rows), 'issues': len(issues), 'issue_groups': len({row.get('category') for row in issues}), 'ready': not issues}


__all__ = ['FILES', 'REQUIRED_MARKERS', 'FORBIDDEN_MARKERS', 'NO_DIRECT_SUBTAB_FUNCTIONS', 'unified_inline_workspace_matrix', 'unified_inline_workspace_summary']
