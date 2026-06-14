# -*- coding: utf-8 -*-
"""Verify Phase 80 manufacturing localization coverage."""
from pathlib import Path
import ast
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
FILES = [
    ROOT / 'alrajhi_client/views/widgets/manufacturing_widget.py',
    ROOT / 'alrajhi_client/views/dialogs/bom_dialog.py',
    ROOT / 'alrajhi_client/views/dialogs/production_order_dialog.py',
    ROOT / 'alrajhi_client/views/dialogs/production_details_dialog.py',
]
REQUIRED_KEYS = [
    'manufacturing_title', 'bom_lists', 'production_orders', 'add_bom',
    'new_production_order', 'bom_recipe', 'new_production_order_title',
    'production_details', 'consume_materials', 'complete_production',
    'status_planned', 'status_in_progress', 'status_completed', 'status_cancelled',
]
ALLOWED_AR_LITERALS = {'منتج نهائي', 'مخزون'}  # persisted domain values; must not be translated in DB filters.

sys.path.insert(0, str(ROOT / 'alrajhi_client'))
from i18n import translate, set_language  # noqa: E402

for lang in ('ar', 'de', 'en'):
    set_language(lang)
    for key in REQUIRED_KEYS:
        value = translate(key)
        if value == key or not value.strip():
            raise SystemExit(f'missing translation for {lang}:{key}')

for file_path in FILES:
    source = file_path.read_text(encoding='utf-8')
    if 'from i18n import translate' not in source:
        raise SystemExit(f'missing i18n import: {file_path}')
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            literal = node.value.strip()
            if re.search(r'[\u0600-\u06ff]', literal) and literal not in ALLOWED_AR_LITERALS:
                raise SystemExit(f'unlocalized Arabic literal in {file_path}:{node.lineno}: {literal!r}')

print('OK phase80 manufacturing localization')
