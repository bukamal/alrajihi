# -*- coding: utf-8 -*-
"""Phase 377 contract: management lists use inline editors instead of sub-tabs."""
from __future__ import annotations

import ast
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parents[3]

TARGETS = {
    'users': {
        'path': 'alrajhi_client/views/widgets/users_widget.py',
        'class': 'UsersWidget',
        'functions': ('add_user', 'edit_user'),
        'forbidden_calls': ('open_user_document', 'open_document_tab', 'open_tab'),
        'required_editor': 'UserDocumentTab',
        'legacy_marker': 'main.open_user_document()',
    },
    'categories': {
        'path': 'alrajhi_client/views/widgets/categories_widget.py',
        'class': 'CategoriesWidget',
        'functions': ('add_category', 'edit_category'),
        'forbidden_calls': ('open_category_document', 'open_document_tab', 'open_tab'),
        'required_editor': 'CategoryEditorTab',
        'legacy_marker': 'main.open_category_document()',
    },
    'warehouses': {
        'path': 'alrajhi_client/views/widgets/warehouses_widget.py',
        'class': 'WarehousesWidget',
        'functions': ('add_warehouse', 'edit_warehouse', 'add_transfer'),
        'forbidden_calls': ('open_warehouse_document', 'open_inventory_transfer_document', 'open_document_tab', 'open_tab'),
        'required_editor': 'WarehouseDocumentTab',
        'legacy_marker': 'main_window.open_warehouse_document()',
    },
    'branches': {
        'path': 'alrajhi_client/views/widgets/branches_widget.py',
        'class': 'BranchesWidget',
        'functions': ('add_branch', 'edit_branch'),
        'forbidden_calls': ('open_branch_document', 'open_document_tab', 'open_tab'),
        'required_editor': 'BranchDocumentTab',
        'legacy_marker': 'main_window.open_branch_document()',
    },
}

REQUIRED_SHARED_MARKERS = (
    'InlineDocumentHostMixin',
    '_install_inline_document_host',
    '_show_inline_document',
    '_connect_inline_detail_preview',
)

HELPER_PATH = 'alrajhi_client/views/widgets/inline_document_host.py'
HELPER_REQUIRED_MARKERS = (
    'ResponsiveMasterDetail',
    'DetailPlaceholder',
    'inline_editor_page',
    'inline_editor_host',
    '_wire_inline_editor_close',
    '_after_inline_document_saved',
)


def _read(path: str, root: Path | None = None) -> str:
    return ((root or ROOT) / path).read_text(encoding='utf-8')


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


def inline_management_editor_matrix(root: Path | None = None) -> List[Dict[str, object]]:
    base = root or ROOT
    rows: List[Dict[str, object]] = []
    helper = _read(HELPER_PATH, base)
    for marker in HELPER_REQUIRED_MARKERS:
        rows.append({
            'key': f'helper:{marker}',
            'category': 'helper',
            'target': 'inline_document_host',
            'status': 'pass' if marker in helper else 'fail',
            'detail': marker,
            'phase': 377,
        })
    for target, spec in TARGETS.items():
        source = _read(spec['path'], base)
        tree = ast.parse(source)
        rows.append({'key': 'parse', 'category': 'source', 'target': target, 'status': 'pass', 'detail': spec['path'], 'phase': 377})
        class_decl = f"class {spec['class']}(InlineDocumentHostMixin, QWidget):"
        rows.append({'key': 'class_mixin', 'category': 'structure', 'target': target, 'status': 'pass' if class_decl in source else 'fail', 'detail': class_decl, 'phase': 377})
        for marker in REQUIRED_SHARED_MARKERS:
            rows.append({'key': f'marker:{marker}', 'category': 'structure', 'target': target, 'status': 'pass' if marker in source else 'fail', 'detail': marker, 'phase': 377})
        rows.append({'key': 'editor_class', 'category': 'editor', 'target': target, 'status': 'pass' if spec['required_editor'] in source else 'fail', 'detail': spec['required_editor'], 'phase': 377})
        rows.append({'key': 'legacy_marker_comment', 'category': 'audit_marker', 'target': target, 'status': 'pass' if spec['legacy_marker'] in source else 'fail', 'detail': spec['legacy_marker'], 'phase': 377})
        for fn in spec['functions']:
            calls = _calls_in_function(tree, fn)
            for call in spec['forbidden_calls']:
                rows.append({
                    'key': f'{fn}:no_{call}',
                    'category': 'no_sub_tabs',
                    'target': target,
                    'status': 'pass' if call not in calls else 'fail',
                    'detail': ','.join(sorted(calls)),
                    'phase': 377,
                })
    return rows


def inline_management_editor_summary(root: Path | None = None) -> Dict[str, object]:
    rows = inline_management_editor_matrix(root)
    issues = [row for row in rows if row.get('status') != 'pass']
    return {
        'phase': 377,
        'checks': len(rows),
        'issues': len(issues),
        'issue_groups': len({row.get('category') for row in issues}),
        'ready': not issues,
    }


__all__ = ['TARGETS', 'inline_management_editor_matrix', 'inline_management_editor_summary']
