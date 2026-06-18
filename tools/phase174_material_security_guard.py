#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 174 guard: material security/settings enforcement."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]

def read(rel):
    return (ROOT / rel).read_text(encoding='utf-8')

def require(cond, msg):
    if not cond:
        print(f"FAIL: {msg}")
        sys.exit(1)

item_editor = read('alrajhi_client/features/items/item_editor_tab.py')
settings = read('alrajhi_client/core/services/settings_service.py')
permissions = read('alrajhi_client/core/services/permission_service.py')
rbac = read('alrajhi_client/core/services/rbac_service.py')
product_service = read('alrajhi_client/core/services/product_service.py')
gateway_contract = read('alrajhi_client/gateways/product_gateway.py')
local_gateway = read('alrajhi_client/gateways/local/product_gateway.py')
remote_gateway = read('alrajhi_client/gateways/remote/product_gateway.py')
rest = read('alrajhi_client/database/connection_rest.py')
server = read('alrajhi_server/repositories/http_route_sql/items.py')
contract = read('alrajhi_client/core/server_control.py')

require('permission_service.can(permission_service.ACTION_EDIT_ITEMS)' in item_editor, 'Material editor must enforce edit_items permission')
require('permission_service.ACTION_PRINT_BARCODES' in item_editor, 'Material editor must enforce barcode print permission')
require('permission_service.ACTION_VIEW_ITEM_COSTS' in item_editor, 'Material editor must enforce cost visibility permission')
require('prevent_opening_quantity_edit_after_activity' in item_editor, 'Opening quantity must be locked after material activity')
require('product_service.item_activity_summary' in item_editor, 'Material editor must use ProductService for activity checks')
require('QSettings' not in item_editor, 'Material editor must not use QSettings directly')
require('ACTION_VIEW_ITEM_COSTS' in permissions and 'ACTION_EDIT_OPENING_STOCK' in permissions, 'PermissionService must expose material cost/opening-stock actions')
require('items.cost.view' in rbac and 'items.opening_stock.edit' in rbac, 'RBAC must expose material cost/opening-stock permissions')
require('hide_cost_for_non_admin' in settings, 'Material settings must expose cost visibility policy')
require('prevent_opening_quantity_edit_after_activity' in settings, 'Material settings must expose opening quantity lock policy')
require('def item_activity_summary' in product_service, 'ProductService must expose item_activity_summary')
require('def activity_summary(self, item_id' in gateway_contract, 'ItemGateway contract must expose activity_summary')
require('def activity_summary(self, item_id' in local_gateway, 'LocalItemGateway must implement activity_summary')
require('def activity_summary(self, item_id' in remote_gateway, 'RemoteItemGateway must implement activity_summary')
require('def get_item_activity_summary' in rest, 'RestClient must expose get_item_activity_summary')
require("@items_bp.route('/items/<int:item_id>/activity-summary'" in server, 'Server must expose material activity-summary endpoint')
require("'/api/items/<int:item_id>/activity-summary'" in contract, 'Remote route contract must include material activity-summary endpoint')
require('material_duplicate_unit_name' in read('alrajhi_client/i18n/translator.py'), 'Phase174 i18n keys must be present')
print('phase174_material_security_guard passed')
