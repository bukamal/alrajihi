# -*- coding: utf-8 -*-
from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'alrajhi_client'))

from i18n.translator import set_language, translate, available_languages, language_direction

REQUIRED = [
    'nav_home','nav_sales','nav_purchases','nav_inventory','nav_manufacturing',
    'dashboard','sales_invoices','purchase_invoices','settings','global_search_placeholder',
    'alerts','theme','logout_confirm','settings_header_title','apply_save_appearance'
]

for code in ('ar','de','en','fr'):
    set_language(code)
    for key in REQUIRED:
        value = translate(key)
        if not value or value == key:
            raise SystemExit(f'missing translation: {code}:{key}')

if [c for c,_ in available_languages()] != ['ar','de','en','fr']:
    raise SystemExit('supported language order must be ar, de, en, fr')
set_language('ar')
if language_direction() != 'rtl':
    raise SystemExit('Arabic must be RTL')
set_language('de')
if language_direction() != 'ltr':
    raise SystemExit('German must be LTR')
set_language('en')
if language_direction() != 'ltr':
    raise SystemExit('English must be LTR')

print('OK: phase77 language migration coverage is valid with French enabled')
