# -*- coding: utf-8 -*-
"""Phase 61 guard: SmartTable must provide enterprise filter/view UX."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
smart = (ROOT / 'alrajhi_client/ui/smart_table_view.py').read_text(encoding='utf-8')
toolbar = (ROOT / 'alrajhi_client/views/widgets/components/table_toolbar.py').read_text(encoding='utf-8')
prefs = (ROOT / 'alrajhi_client/views/widgets/components/table_preferences.py').read_text(encoding='utf-8')

required_smart = [
    'class FilterBuilderDialog',
    'def set_column_filters',
    'def clear_filters',
    'def save_view_preset',
    'def apply_view_preset',
    'def view_preset_names',
    'filterAcceptsRow',
]
required_toolbar = [
    'filtersRequested',
    'saveViewRequested',
    'filter_btn',
    '_show_filters',
    '_save_view',
]
required_prefs = [
    'save_named_view',
    'load_named_view',
    'named_view_names',
    'save_value',
    'load_value',
]
missing = []
for token in required_smart:
    if token not in smart:
        missing.append(f'SmartTableView missing {token}')
for token in required_toolbar:
    if token not in toolbar:
        missing.append(f'TableToolbar missing {token}')
for token in required_prefs:
    if token not in prefs:
        missing.append(f'TablePreferences missing {token}')
if missing:
    print('Enterprise filter UX guard failed:')
    for item in missing:
        print(' -', item)
    sys.exit(1)
print('Enterprise filter UX guard passed.')
