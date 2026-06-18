#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Guard Phase 53 category/settings document-tab refactor."""
from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = [
    ROOT / 'alrajhi_client/features/categories/category_editor_tab.py',
    ROOT / 'alrajhi_client/features/categories/components/category_panels.py',
    ROOT / 'alrajhi_client/features/settings/settings_document_tabs.py',
    ROOT / 'alrajhi_client/features/settings/__init__.py',
    ROOT / 'alrajhi_client/views/main_window.py',
]


def main() -> int:
    errors: list[str] = []
    for path in FILES:
        if not path.exists():
            errors.append(f'missing {path.relative_to(ROOT)}')
            continue
        try:
            ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
        except SyntaxError as exc:
            errors.append(f'syntax error in {path.relative_to(ROOT)}:{exc.lineno}: {exc.msg}')

    cat_text = (ROOT / 'alrajhi_client/features/categories/category_editor_tab.py').read_text(encoding='utf-8')
    cat_panels = (ROOT / 'alrajhi_client/features/categories/components/category_panels.py').read_text(encoding='utf-8')
    settings_text = (ROOT / 'alrajhi_client/features/settings/settings_document_tabs.py').read_text(encoding='utf-8')
    main_text = (ROOT / 'alrajhi_client/views/main_window.py').read_text(encoding='utf-8')

    for token in ('CategoryHeaderPanel', 'CategoryPropertiesPanel', 'product_service.add_category', 'product_service.update_category'):
        if token not in cat_text + cat_panels:
            errors.append(f'category document refactor missing token: {token}')

    for token in (
        'class SettingsSectionDocumentTab(BaseDocumentTab)',
        'CompanySettingsTab',
        'AccountingSettingsTab',
        'InventorySettingsTab',
        'RestaurantSettingsTab',
        'PrintingSettingsTab',
        'UISettingsTab',
        'SecuritySettingsTab',
        'SETTINGS_SECTION_TABS',
        'settings_service.set',
    ):
        if token not in settings_text:
            errors.append(f'settings document tab missing token: {token}')

    for banned in ('DatabaseConnection', '.execute(', 'SettingsRepository('):
        if banned in settings_text:
            errors.append(f'settings document tab violates service boundary: {banned}')

    for token in ('def open_settings_section_document', 'from features.settings import SETTINGS_SECTION_TABS', "settings:{section}", "item.key.startswith('settings:')"):
        if token not in main_text:
            errors.append(f'main_window missing settings workspace integration: {token}')

    if errors:
        print('Phase 53 document settings/categories guard failed:')
        for error in errors:
            print(f' - {error}')
        return 1
    print('Phase 53 document settings/categories guard passed.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
