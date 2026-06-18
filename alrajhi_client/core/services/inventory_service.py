# -*- coding: utf-8 -*-
"""Inventory movement service.

The legacy code has both inventory_dao and inventory_movement_dao wrappers. This
service is the stable import point for new code and for repository-side inventory
posting, without deleting the old compatibility modules yet.
"""
from __future__ import annotations

from typing import Dict, List

from core.compat import records
from gateways.inventory_gateway import create_inventory_gateway
from core.services.audit_service import audit_service
from core.services.inventory_operation_policy import inventory_operation_policy


class InventoryService:
    def __init__(self):
        self.gateway = create_inventory_gateway()

    def movements(self, item_id: int) -> List[Dict]:
        return records(self.gateway.movements(item_id), 'movements')

    def ledger_entries(self, **filters) -> List[Dict]:
        inventory_operation_policy.require(inventory_operation_policy.OP_LEDGER_VIEW, context='inventory_service.ledger_entries', payload=filters)
        return records(self.gateway.ledger_entries(**filters), 'ledger')

    def record_ledger_entry(self, **data):
        system_refs = {'invoice', 'sales_return', 'purchase_return', 'warehouse_movement', 'warehouse_transfer', 'warehouse_transfer_cancel', 'production_order', 'manufacturing', 'restaurant', 'pos'}
        if data.get('reference_type') not in system_refs:
            inventory_operation_policy.require(inventory_operation_policy.OP_DIRECT_MOVEMENT, context='inventory_service.record_ledger_entry', payload=data)
        entry_id = self.gateway.record_ledger_entry(data)
        audit_service.log(
            'POST', 'INVENTORY_LEDGER', entry_id,
            new_values=data,
            details='تسجيل قيد دفتر مخزون'
        )
        return entry_id

    def ledger_balance(self, item_id: int, warehouse_id=None):
        return self.gateway.ledger_balance(item_id, warehouse_id)

    def ledger_reconciliation(self, item_id=None, warehouse_id=None, tolerance='0') -> Dict:
        inventory_operation_policy.require(inventory_operation_policy.OP_RECONCILE, context='inventory_service.ledger_reconciliation', payload={'item_id': item_id, 'warehouse_id': warehouse_id})
        """Compare operational stock with shadow inventory ledger balances.

        Phase 27 is diagnostic-only. It does not change stock quantities and does
        not make the ledger authoritative.
        """
        return self.gateway.ledger_reconciliation(item_id=item_id, warehouse_id=warehouse_id, tolerance=tolerance)

    def ledger_dual_read(self, item_id=None, warehouse_id=None, tolerance='0', include_matches=True) -> Dict:
        """Return operational and shadow-ledger balances side by side.

        Phase 31 diagnostic-only dual-read mode. The operational stock remains
        authoritative; the ledger is only compared.
        """
        return self.gateway.ledger_dual_read(item_id=item_id, warehouse_id=warehouse_id, tolerance=tolerance, include_matches=include_matches)

    def ledger_snapshot(self, item_id=None, warehouse_id=None) -> Dict:
        """Return a read-only shadow-ledger balance snapshot. Phase 30 diagnostic-only."""
        return self.gateway.ledger_snapshot(item_id=item_id, warehouse_id=warehouse_id)

    def ledger_health(self, item_id=None, warehouse_id=None, tolerance='0') -> Dict:
        """Return Phase 30 shadow-ledger readiness diagnostics. Read-only."""
        return self.gateway.ledger_health(item_id=item_id, warehouse_id=warehouse_id, tolerance=tolerance)

    def ledger_readiness(self, item_id=None, warehouse_id=None, tolerance='0') -> Dict:
        """Return Phase 33 read-only gate for controlled ledger-read adoption."""
        return self.gateway.ledger_readiness(item_id=item_id, warehouse_id=warehouse_id, tolerance=tolerance)

    def ledger_controlled_read(self, item_id=None, warehouse_id=None, mode=None, tolerance='0') -> Dict:
        """Phase 34 controlled stock-read decision.

        Default remains operational stock.  When mode is ledger_trial, the
        gateway may select ledger balances only if readiness approves.  This
        method is still read-only and does not update any quantities.
        """
        if mode is None:
            try:
                from core.services.settings_service import settings_service
                mode = settings_service.get('inventory/stock_read_mode', 'operational')
            except Exception:
                mode = 'operational'
        return self.gateway.ledger_controlled_read(item_id=item_id, warehouse_id=warehouse_id, mode=mode, tolerance=tolerance)

    def ledger_backfill(self, dry_run=True, item_id=None, warehouse_id=None, clear_existing=False, include_item_movements=True, include_warehouse_movements=True) -> Dict:
        inventory_operation_policy.require(inventory_operation_policy.OP_LEDGER_BACKFILL, context='inventory_service.ledger_backfill', payload={'dry_run': dry_run, 'item_id': item_id, 'warehouse_id': warehouse_id, 'clear_existing': clear_existing})
        """Backfill shadow ledger from legacy inventory movements.

        Phase 28 migration-preparation only. The operation never changes current
        operational stock quantities. Use dry_run=True first.
        """
        return self.gateway.ledger_backfill(
            dry_run=dry_run,
            item_id=item_id,
            warehouse_id=warehouse_id,
            clear_existing=clear_existing,
            include_item_movements=include_item_movements,
            include_warehouse_movements=include_warehouse_movements,
        )

    def record_movement(self, item_id: int, movement_type: str, quantity, unit_cost, reference_id=None):
        inventory_operation_policy.require(inventory_operation_policy.OP_DIRECT_MOVEMENT, context='inventory_service.record_movement', payload={'item_id': item_id, 'movement_type': movement_type, 'quantity': str(quantity), 'reference_id': reference_id})
        movement_id = self.gateway.record_movement(item_id, movement_type, quantity, unit_cost, reference_id)
        audit_service.log(
            'POST', 'INVENTORY_MOVEMENT', movement_id,
            new_values={
                'item_id': item_id, 'movement_type': movement_type,
                'quantity': str(quantity), 'unit_cost': str(unit_cost),
                'reference_id': reference_id
            },
            details='تسجيل حركة مخزون'
        )
        return movement_id


inventory_service = InventoryService()
