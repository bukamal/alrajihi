#!/usr/bin/env python3
from __future__ import annotations
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = [
    ROOT / 'alrajhi_client' / 'core' / 'services' / 'global_search_service.py',
    ROOT / 'alrajhi_client' / 'shell' / 'quick_open_dialog.py',
    ROOT / 'alrajhi_client' / 'views' / 'main_window.py',
]
SQL_WORDS = ('SELECT ', 'INSERT ', 'UPDATE ', 'DELETE ', 'CREATE ', 'ALTER ', 'DROP ')

def main() -> int:
    errors = []
    for path in FILES:
        if not path.exists():
            errors.append(f'missing {path.relative_to(ROOT)}')
            continue
        text = path.read_text(encoding='utf-8')
        try:
            ast.parse(text, filename=str(path))
        except SyntaxError as exc:
            errors.append(f'{path.relative_to(ROOT)} syntax error: {exc}')
        if path.name == 'global_search_service.py' and any(word in text.upper() for word in SQL_WORDS):
            errors.append('global_search_service must not contain SQL literals')
    main_text = (ROOT / 'alrajhi_client' / 'views' / 'main_window.py').read_text(encoding='utf-8')
    required = ['global_search_service.search', '_global_search_items', '_open_quick_open_item', 'open_item_document', 'open_party_document', 'open_quick_invoice']
    for token in required:
        if token not in main_text:
            errors.append(f'missing workspace search hook: {token}')
    quick_text = (ROOT / 'alrajhi_client' / 'shell' / 'quick_open_dialog.py').read_text(encoding='utf-8')
    for token in ['search_provider', 'payload', 'QuickOpenItem']:
        if token not in quick_text:
            errors.append(f'missing quick-open capability: {token}')
    if errors:
        print('Global search guard failed:')
        for e in errors:
            print(' -', e)
        return 1
    print('Global search guard passed.')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
