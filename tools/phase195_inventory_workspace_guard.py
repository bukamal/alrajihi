# -*- coding: utf-8 -*-
"""Guard for Phase 195 inventory / warehouse workspace professionalization."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
widget = ROOT / 'alrajhi_client' / 'views' / 'widgets' / 'warehouses_widget.py'
schema = ROOT / 'alrajhi_client' / 'features' / 'inventory' / 'inventory_workspace_schema.py'
translator = ROOT / 'alrajhi_client' / 'i18n' / 'translator.py'

text = widget.read_text(encoding='utf-8')
schema_text = schema.read_text(encoding='utf-8')
tr_text = translator.read_text(encoding='utf-8')

required_widget_tokens = [
    'from features.inventory.inventory_workspace_schema import',
    "self.wh_preset = self._toolbar_preset_combo('warehouses')",
    "self.balance_stock_filter = QComboBox()",
    "self.mov_type_filter = QComboBox()",
    "self.transfer_status_filter = QComboBox()",
    'def _apply_workspace_preset(self, target: str):',
    'def _source_row_for_table(self, table):',
    'current_source_row',
    "headers, keys = headers_and_keys(columns_for('warehouses'))",
    "headers, keys = headers_and_keys(columns_for('balances'))",
    "headers, keys = headers_and_keys(columns_for('movements'))",
    "headers, keys = headers_and_keys(columns_for('transfers'))",
    "self._apply_workspace_preset('warehouses')",
    "self._apply_workspace_preset('balances')",
    "self._apply_workspace_preset('movements')",
    "self._apply_workspace_preset('transfers')",
]
missing = [token for token in required_widget_tokens if token not in text]
if missing:
    raise SystemExit('WarehousesWidget missing Phase195 tokens: ' + ', '.join(missing))

if 'return self.transfer_model.get_id(idx.row())' in text or 'return self.wh_model.get_id(idx.row())' in text:
    raise SystemExit('Phase195 source-row-safe selection was not applied to warehouse/transfer ids.')

required_schema_tokens = [
    'def warehouse_columns()',
    'def balance_columns()',
    'def movement_columns()',
    'def transfer_columns()',
    'def inventory_workspace_preset_names()',
    'def visible_keys_for(kind: str, preset: str)',
]
missing_schema = [token for token in required_schema_tokens if token not in schema_text]
if missing_schema:
    raise SystemExit('Inventory workspace schema incomplete: ' + ', '.join(missing_schema))

required_translation_keys = [
    'inventory_workspace_preset_compact',
    'inventory_workspace_preset_warehouse',
    'inventory_workspace_preset_accountant',
    'inventory_workspace_preset_manager',
    'inventory_stock_status',
    'inventory_search_movements',
    'inventory_search_transfers',
    'inventory_movement_all_types',
    'from_warehouse_clean',
    'to_warehouse_clean',
    'phase195_inventory_workspace_professionalized',
]
missing_tr = [key for key in required_translation_keys if key not in tr_text]
if missing_tr:
    raise SystemExit('Phase195 translation keys missing: ' + ', '.join(missing_tr))

print('phase195_inventory_workspace_guard passed')
