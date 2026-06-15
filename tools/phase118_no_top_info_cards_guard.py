# -*- coding: utf-8 -*-
"""Guard: page widgets must not insert top explanatory/header cards.

This is intentionally source-level because the CI environment may not have Qt.
"""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
WIDGETS = ROOT / 'alrajhi_client' / 'views' / 'widgets'
FAIL = []

# apply_modern_widget must not insert ModernPageHeader on pages.
modern = WIDGETS / 'modern_ui.py'
text = modern.read_text(encoding='utf-8')
if "layout.insertWidget(0, _make_header(title, subtitle))" in text:
    FAIL.append('modern_ui.apply_modern_widget still inserts ModernPageHeader')

# These object names denote page-level top explanatory cards, not functional section cards.
for path in WIDGETS.glob('*.py'):
    if path.name == 'modern_ui.py':
        continue
    src = path.read_text(encoding='utf-8')
    forbidden = [
        "setObjectName('ModernPageHeader')",
        'setObjectName("ModernPageHeader")',
        "setObjectName('settingsHeader')",
        'setObjectName("settingsHeader")',
    ]
    for token in forbidden:
        if token in src:
            FAIL.append(f'{path.relative_to(ROOT)} contains {token}')

# Settings must not add a custom header before tabs.
settings = (WIDGETS / 'settings_widget.py').read_text(encoding='utf-8')
if 'main.addWidget(self._create_header())' in settings:
    FAIL.append('settings_widget still adds _create_header at top')

if FAIL:
    print('phase118_no_top_info_cards_guard: FAIL')
    for item in FAIL:
        print('-', item)
    raise SystemExit(1)
print('phase118_no_top_info_cards_guard: PASS')
