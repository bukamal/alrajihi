# -*- coding: utf-8 -*-
from __future__ import annotations
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
item_tab = ROOT / 'alrajhi_client/features/items/item_editor_tab.py'
settings = ROOT / 'alrajhi_client/core/services/settings_service.py'
product = ROOT / 'alrajhi_client/core/services/product_service.py'
dashboard = ROOT / 'alrajhi_client/views/widgets/dashboard_widget.py'
connection = ROOT / 'alrajhi_client/database/connection.py'

errors = []
text = item_tab.read_text(encoding='utf-8')
for token in [
    'class MaterialDocumentTab',
    'ItemEditorTab = MaterialDocumentTab',
    'barcode_service',
    'barcode_input_service',
    'barcode_label_service',
    'settings_service.get_material_settings',
    'BarcodeCameraDialog',
    'labels_document_html',
    'workspace_print',
    'UNIT_COL_BARCODE',
]:
    if token not in text:
        errors.append(f'missing item editor token: {token}')
if 'QSettings' in text:
    errors.append('MaterialDocumentTab must not use QSettings directly')
if 'from views.dialogs.item_dialog import ItemDialog' in dashboard.read_text(encoding='utf-8'):
    errors.append('Dashboard still opens legacy ItemDialog for add-item shortcut')
if 'def get_material_settings' not in settings.read_text(encoding='utf-8'):
    errors.append('settings_service.get_material_settings is missing')
if "def generate_barcode(self, symbology: str = 'EAN13', prefix" not in product.read_text(encoding='utf-8'):
    errors.append('product_service.generate_barcode must accept prefix for settings-driven EAN13/CODE128 generation')
conn = connection.read_text(encoding='utf-8')
if re.search(r'FROM items i\s+FROM items i', conn):
    errors.append('database connection has duplicate FROM items i in barcode lookup')
if errors:
    raise SystemExit('\n'.join(errors))
print('phase171_material_document_guard passed')
