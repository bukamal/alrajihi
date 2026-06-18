#!/usr/bin/env python3
"""Guard for Phase 46 document-tab migration.

Large business editors must open as workspace document tabs, not as modal-only
QDialog flows. The guard checks the foundation and the first converted domains.
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = [
    ROOT / 'alrajhi_client' / 'workspace' / 'documents' / 'base_document_tab.py',
    ROOT / 'alrajhi_client' / 'features' / 'items' / 'item_editor_tab.py',
    ROOT / 'alrajhi_client' / 'features' / 'categories' / 'category_editor_tab.py',
]


def fail(message: str) -> int:
    print('Document tabs guard failed:')
    print(f' - {message}')
    return 1


def main() -> int:
    for path in REQUIRED:
        if not path.exists():
            return fail(f'missing {path.relative_to(ROOT)}')
        try:
            ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
        except SyntaxError as exc:
            return fail(f'syntax error in {path.relative_to(ROOT)}:{exc.lineno}: {exc.msg}')

    main_window = ROOT / 'alrajhi_client' / 'views' / 'main_window.py'
    text = main_window.read_text(encoding='utf-8')
    required_tokens = [
        'def open_item_document',
        'def open_category_document',
        'features.items',
        'features.categories',
        'workspace.open_tab',
    ]
    missing = [token for token in required_tokens if token not in text]
    if missing:
        return fail(f'main_window missing document-tab integration tokens: {missing}')

    items_widget = (ROOT / 'alrajhi_client' / 'views' / 'widgets' / 'items_widget.py').read_text(encoding='utf-8')
    if 'main.open_item_document' not in items_widget:
        return fail('ItemsWidget add/edit does not route to item document tabs')

    categories_widget = (ROOT / 'alrajhi_client' / 'views' / 'widgets' / 'categories_widget.py').read_text(encoding='utf-8')
    if 'main.open_category_document' not in categories_widget:
        return fail('CategoriesWidget add/edit does not route to category document tabs')

    print('Document tabs guard passed: item/category editors use workspace document tabs.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
