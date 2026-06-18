#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Guard for Phase 58 invoice grid/table UX.

Verifies that invoice creation/editing uses an extended table-centered layout,
that actions live in a bottom action bar, and that SmartTableView supports
enterprise column behavior required by ERP users.
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
errors = []

invoice = ROOT / 'alrajhi_client' / 'views' / 'dialogs' / 'invoice_dialog.py'
smart = ROOT / 'alrajhi_client' / 'ui' / 'smart_table_view.py'

invoice_text = invoice.read_text(encoding='utf-8')
layout = ROOT / 'alrajhi_client' / 'features' / 'transactions' / 'components' / 'transaction_document_layout.py'
layout_text = layout.read_text(encoding='utf-8') if layout.exists() else ''
invoice_layout_text = invoice_text + '\n' + layout_text
smart_text = smart.read_text(encoding='utf-8')

required_invoice = {
    'TransactionLineGrid': 'invoice lines must use the shared transaction grid foundation',
    'TransactionDocumentLayout': 'invoice body must use the shared transaction document layout',
    'BottomActionBar': 'invoice actions must be placed below the document body',
    'content_splitter = QSplitter(Qt.Horizontal)': 'invoice body must resize with a splitter',
    'setMinimumHeight(440)': 'invoice grid must be the dominant extended area',
    'sectionMoved.connect(lambda *_: self._save_lines_table_layout())': 'column reordering must persist',
}
for token, msg in required_invoice.items():
    if token not in invoice_layout_text:
        errors.append(f'invoice_dialog.py: missing {msg}')

if 'title_layout.addWidget(btn)' in invoice_text:
    errors.append('invoice_dialog.py: primary invoice actions are still added to top title bar')
if invoice_text.count('left_layout.addWidget(self.lines_table') != 1:
    errors.append('invoice_dialog.py: invoice lines table should be added exactly once')

required_smart = {
    'setSectionsMovable(True)': 'column drag/reorder support',
    'set_column_visible': 'column hide/show support',
    'save_layout': 'layout persistence support',
    'restore_layout': 'layout restore support',
    'fit_columns_to_view': 'responsive column fitting',
    'resizeEvent': 'window resize adaptation',
    'Responsive columns': 'user-visible responsive columns toggle',
}
for token, msg in required_smart.items():
    if token not in smart_text:
        errors.append(f'smart_table_view.py: missing {msg}')

if errors:
    print('Invoice/grid UX guard failed:')
    for e in errors:
        print(f' - {e}')
    sys.exit(1)
print('Invoice/grid UX guard passed.')
