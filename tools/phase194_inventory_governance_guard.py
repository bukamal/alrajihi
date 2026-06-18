# -*- coding: utf-8 -*-
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def read(rel):
    return (ROOT / rel).read_text(encoding='utf-8')

def assert_contains(rel, needles):
    text = read(rel)
    for needle in needles:
        assert needle in text, f"Missing {needle!r} in {rel}"

assert_contains('alrajhi_client/core/services/inventory_operation_policy.py', [
    'class InventoryOperationPolicy',
    'OP_TRANSFER_CREATE',
    'OP_LEDGER_BACKFILL',
    'permission_service.ACTION_INVENTORY_TRANSFER_CREATE',
])
assert_contains('alrajhi_client/core/services/settings_service.py', [
    "'operations': {",
    "'allow_transfer_create'",
    "'stock_read_mode'",
])
assert_contains('alrajhi_client/core/services/warehouse_service.py', [
    'inventory_operation_policy.require(inventory_operation_policy.OP_WAREHOUSE_CREATE',
    'inventory_operation_policy.require(inventory_operation_policy.OP_TRANSFER_CREATE',
    'system_refs =',
])
assert_contains('alrajhi_client/core/services/inventory_service.py', [
    'OP_LEDGER_VIEW',
    'OP_LEDGER_BACKFILL',
    'OP_DIRECT_MOVEMENT',
])
assert_contains('alrajhi_client/core/services/permission_service.py', [
    'ACTION_USE_INVENTORY',
    'ACTION_INVENTORY_TRANSFER_CREATE',
    'inventory.ledger.backfill',
])
assert_contains('alrajhi_client/core/services/rbac_service.py', [
    'inventory.use',
    'inventory.transfer.create',
    'inventory.ledger.backfill',
])
assert_contains('alrajhi_client/views/widgets/warehouses_widget.py', [
    '_apply_inventory_operation_state',
    '_require_inventory_operation',
    'OP_TRANSFER_CANCEL',
])
assert_contains('alrajhi_client/database/migrations.py', ['Phase194: Inventory / warehouse operation-level permissions', 'inventory.warehouse.create'])
assert_contains('alrajhi_server/database/migrations.py', ['Phase194: Inventory / warehouse operation-level permissions', 'inventory.warehouse.create'])
print('phase194_inventory_governance_guard passed')
