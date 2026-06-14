# -*- coding: utf-8 -*-
from pathlib import Path
import re, sys
ROOT = Path(__file__).resolve().parents[1]
checks = {
    'alrajhi_client/views/widgets/components/table_toolbar.py': [
        'إضافة ', 'تعديل', 'حذف', 'الأعمدة', 'طباعة', 'تحديث', ' سجل', 'إعادة ضبط الأعمدة',
    ],
}
errors=[]
for rel, bads in checks.items():
    text=(ROOT/rel).read_text(encoding='utf-8')
    for b in bads:
        if b in text:
            errors.append(f'{rel}: hardcoded UI text remains: {b!r}')
# ensure ItemsWidget has dynamic headers and buttons
it=(ROOT/'alrajhi_client/views/widgets/items_widget.py').read_text(encoding='utf-8')
for needle in ['def _display_headers', 'def _extra_buttons', 'self.display_headers = self._display_headers()']:
    if needle not in it:
        errors.append(f'items_widget.py missing {needle}')
tr=(ROOT/'alrajhi_client/i18n/translator.py').read_text(encoding='utf-8')
for k in ['add_entity','columns','reset_columns','column_number','records_count']:
    if k not in tr:
        errors.append(f'translator missing {k}')
if errors:
    print('\n'.join(errors))
    sys.exit(1)
print('OK: Phase 92 controls localization guard passed')
