# -*- coding: utf-8 -*-
"""Phase 173 material workspace governance guard."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(rel):
    return (ROOT / rel).read_text(encoding='utf-8')


def require(condition, message):
    if not condition:
        raise SystemExit(f"Phase173 guard failed: {message}")


items_widget = read('alrajhi_client/views/widgets/items_widget.py')
require('ItemDialog' not in items_widget, 'ItemsWidget must not import/open legacy ItemDialog')
require('material_list_schema' in items_widget, 'ItemsWidget must use the material list column schema')
require('material_visible_keys_for_preset' in items_widget, 'Material list presets must be applied')
require('permission_service.ACTION_EDIT_ITEMS' in items_widget, 'ItemsWidget must use item-specific edit permission')
require('permission_service.ACTION_PRINT_BARCODES' in items_widget, 'Barcode printing must check barcode permission')
require('selected_source_rows' in items_widget, 'Barcode action must respect SmartTable proxy/source rows')
require('settings_service.set(self._pref_key' in items_widget, 'Material grid view must persist through settings_service')

schema = read('alrajhi_client/features/items/material_list_schema.py')
for key in ('cashier', 'warehouse', 'accountant', 'manager'):
    require(key in schema, f'Missing material preset: {key}')
for col in ('barcode', 'category', 'available_quantity', 'unit_cost'):
    require(col in schema, f'Missing material list column: {col}')

prefs = read('alrajhi_client/views/widgets/components/table_preferences.py')
require('from PyQt5.QtCore import QSettings' not in prefs and 'QSettings(' not in prefs, 'Generic table preferences must not instantiate QSettings directly')
require('settings_service' in prefs, 'Generic table preferences must use settings_service')
require('users/{user_id}/branches/{branch_id}/profiles/{profile_id}' in prefs, 'Table preferences must be user/branch/profile scoped')

remote = read('alrajhi_client/gateways/remote/product_gateway.py')
require('get_item_sold_quantities' in remote, 'Remote item gateway must use sold quantities API')
require("return {i: Decimal('0') for i in ids}" in remote, 'Remote sold quantities fallback must remain safe')

rest = read('alrajhi_client/database/connection_rest.py')
require('/api/items/sold-quantities' in rest, 'RestClient must expose item sold quantities endpoint')
server = read('alrajhi_server/repositories/http_route_sql/items.py')
require("@items_bp.route('/items/sold-quantities'" in server, 'Server must expose item sold quantities endpoint')
contract = read('alrajhi_client/core/server_control.py')
require("'/api/items/sold-quantities'" in contract, 'Remote route contract must include sold quantities endpoint')

print('Phase173 material workspace guard passed')
