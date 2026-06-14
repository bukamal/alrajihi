# -*- coding: utf-8 -*-
"""Phase 84 guard: settings page localization cleanup."""
from __future__ import annotations
import ast
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / 'alrajhi_client'
sys.path.insert(0, str(CLIENT))
from i18n.translator import set_language, translate

SETTINGS = ROOT / 'alrajhi_client' / 'views' / 'widgets' / 'settings_widget.py'
AR_RE = re.compile(r'[\u0600-\u06FF]')
ALLOWED_AR_LITERALS = set()
REQUIRED_KEYS = [
    'settings_pos_title', 'settings_company_title', 'settings_print_templates_title',
    'settings_currency_title', 'settings_rates_title', 'settings_network_title',
    'settings_backup_title', 'settings_database_admin_title',
    'settings_network_test_success', 'settings_backup_created_integrity',
]


def arabic_literals(path: Path) -> list[str]:
    tree = ast.parse(path.read_text('utf-8'), filename=str(path))
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            text = node.value.strip()
            if AR_RE.search(text) and text not in ALLOWED_AR_LITERALS:
                found.append(text)
    return found


def main() -> int:
    found = arabic_literals(SETTINGS)
    if found:
        print('Arabic literals remain in settings_widget.py:')
        for text in found[:40]:
            print('-', text)
        return 1
    for lang in ('ar', 'de', 'en'):
        set_language(lang)
        missing = [k for k in REQUIRED_KEYS if translate(k) == k]
        if missing:
            print(f'Missing phase84 translations for {lang}: {missing}')
            return 1
    print('OK phase84 settings localization cleanup')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
