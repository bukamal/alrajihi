# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / 'alrajhi_client'

sys.path.insert(0, str(CLIENT))

from i18n.translator import SUPPORTED_LANGUAGES, translate, set_language, normalize_language, language_direction


def fail(msg: str):
    raise SystemExit(f"FAIL: {msg}")


def main():
    expected = ('ar', 'de', 'en', 'fr')
    if tuple(SUPPORTED_LANGUAGES) != expected:
        fail(f"supported languages must be {expected}, got {SUPPORTED_LANGUAGES}")
    if normalize_language('fr') != 'fr':
        fail('French code must normalize to fr')
    if language_direction('ar') != 'rtl' or any(language_direction(code) != 'ltr' for code in ('de','en','fr')):
        fail('language direction mapping is invalid')
    for lang in expected:
        set_language(lang)
        for key in ('app_title', 'login', 'username', 'password', 'save', 'cancel'):
            value = translate(key)
            if not value or value == key:
                fail(f'missing translation for {key} in {lang}')

    login = CLIENT / 'views' / 'dialogs' / 'login_dialog.py'
    text = login.read_text(encoding='utf-8')
    forbidden = []
    for token in forbidden:
        if token in text:
            fail(f'unexpected language token remains in login dialog: {token}')
    if 'available_languages()' not in text:
        fail('login dialog must populate language combo from central language registry')

    settings = CLIENT / 'views' / 'widgets' / 'settings_widget.py'
    st = settings.read_text(encoding='utf-8')
    if 'settings_service.save_language_settings' not in st and 'settings_service.set_language' not in st:
        fail('settings appearance tab must persist selected language')
    if 'available_languages()' not in st:
        fail('settings appearance tab must use central language registry')

    printing = CLIENT / 'printing' / 'print_templates.py'
    pt = printing.read_text(encoding='utf-8')
    if "<html dir='ltr' lang='ar'>" in pt or 'direction: ltr;' in pt:
        fail('print template still hard-codes Arabic as LTR')
    if '_document_direction' not in pt:
        fail('print template must resolve language direction centrally')

    print('OK: language foundation supports Arabic, German, English and French with RTL/LTR baseline')


if __name__ == '__main__':
    main()
