# -*- coding: utf-8 -*-
"""Verify that windows/dialogs containing tables or tabs are covered by the safe design-system layer."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGETS = [ROOT / 'alrajhi_client' / 'views', ROOT / 'alrajhi_client' / 'printing']
NEEDLES = ('QTableWidget', 'QTableView', 'QTreeWidget', 'QTreeView', 'QTabWidget')
COVERAGE_MARKERS = (
    'apply_modern_widget',
    'apply_modern_dialog',
    'apply_modern_item_style',
    '_apply_modern_invoice_style',
    'CustomTableView',
    'ThemeManager.get_stylesheet()',
)

missing = []
for base in TARGETS:
    if not base.exists():
        continue
    for path in base.rglob('*.py'):
        if '__pycache__' in path.parts:
            continue
        text = path.read_text(encoding='utf-8', errors='ignore')
        if any(n in text for n in NEEDLES):
            if not any(m in text for m in COVERAGE_MARKERS):
                missing.append(path.relative_to(ROOT).as_posix())

if missing:
    print('UNCOVERED TABLE/TAB FILES:')
    for item in missing:
        print('-', item)
    raise SystemExit(1)
print('OK: all table/tab windows have safe design-system coverage markers')
