#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Static coverage check for table/tab design-system wiring."""
from __future__ import annotations

import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / 'alrajhi_client'
TABLE_NAMES = {'QTableWidget', 'QTableView', 'QTreeWidget', 'QTreeView'}
TAB_NAMES = {'QTabWidget'}
BAD_COLOR_RE = re.compile(r'#[0-9A-Fa-f]{3,8}|rgba?\(')


def iter_py():
    for path in CLIENT.rglob('*.py'):
        if '__pycache__' not in path.parts:
            yield path


def main():
    table_sites = []
    tab_sites = []
    local_table_tab_styles = []
    for path in iter_py():
        text = path.read_text(encoding='utf-8', errors='ignore')
        rel = path.relative_to(ROOT)
        try:
            tree = ast.parse(text)
        except SyntaxError as exc:
            raise SystemExit(f'SYNTAX ERROR {rel}: {exc}')
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                name = ''
                if isinstance(node.func, ast.Name):
                    name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    name = node.func.attr
                if name in TABLE_NAMES:
                    table_sites.append((str(rel), node.lineno, name))
                if name in TAB_NAMES:
                    tab_sites.append((str(rel), node.lineno, name))
        # Flag only local styles that explicitly target table/tab selectors with literal colors.
        if 'setStyleSheet' in text and any(sel in text for sel in ['QTableWidget', 'QTableView', 'QTabWidget', 'QTabBar']):
            if BAD_COLOR_RE.search(text):
                local_table_tab_styles.append(str(rel))

    required = [
        CLIENT / 'theme' / 'widget_polish.py',
        CLIENT / 'theme' / 'qss.py',
        CLIENT / 'theme_manager.py',
    ]
    missing = [str(p.relative_to(ROOT)) for p in required if not p.exists()]
    if missing:
        raise SystemExit('Missing design-system files: ' + ', '.join(missing))
    tm = (CLIENT / 'theme_manager.py').read_text(encoding='utf-8')
    if 'install_design_system_polish' not in tm:
        raise SystemExit('ThemeManager does not install table/tab runtime polish')
    qss = (CLIENT / 'theme' / 'qss.py').read_text(encoding='utf-8')
    for selector in ['QTableView, QTableWidget', 'QHeaderView::section', 'QTabWidget::pane', 'QTabBar::tab']:
        if selector not in qss:
            raise SystemExit('Missing QSS selector: ' + selector)
    print('OK table/tab design-system coverage')
    print(f'table/tree sites: {len(table_sites)}')
    print(f'tab sites: {len(tab_sites)}')
    if local_table_tab_styles:
        print('local table/tab stylesheet files retained for compatibility:')
        for item in sorted(set(local_table_tab_styles)):
            print(' - ' + item)


if __name__ == '__main__':
    main()
