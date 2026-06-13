# -*- coding: utf-8 -*-
"""Remote API inventory movement gateway adapter."""
from __future__ import annotations

from typing import Any, Dict, List

from gateways.inventory_gateway import InventoryGateway


class RemoteInventoryGateway(InventoryGateway):
    def __init__(self, rest_client):
        self.rest_client = rest_client

    def movements(self, item_id: int) -> List[Dict[str, Any]]:
        return self.rest_client.get_inventory_movements(item_id)

    def record_movement(self, item_id: int, movement_type: str, quantity,
                        unit_cost, reference_id=None) -> int | None:
        return self.rest_client.record_inventory_movement({
            'item_id': item_id,
            'movement_type': movement_type,
            'quantity': quantity,
            'unit_cost': unit_cost,
            'reference_id': reference_id,
        })

    def ledger_entries(self, **filters) -> List[Dict[str, Any]]:
        return self.rest_client.get_inventory_ledger(**filters)

    def record_ledger_entry(self, data: Dict[str, Any]) -> int | None:
        return self.rest_client.record_inventory_ledger_entry(data)

    def ledger_balance(self, item_id: int, warehouse_id=None):
        return self.rest_client.get_inventory_ledger_balance(item_id, warehouse_id=warehouse_id)

    def ledger_reconciliation(self, item_id=None, warehouse_id=None, tolerance='0') -> Dict[str, Any]:
        return self.rest_client.get_inventory_ledger_reconciliation(item_id=item_id, warehouse_id=warehouse_id, tolerance=tolerance)

    def ledger_dual_read(self, item_id=None, warehouse_id=None, tolerance='0', include_matches=True) -> Dict[str, Any]:
        return self.rest_client.get_inventory_ledger_dual_read(item_id=item_id, warehouse_id=warehouse_id, tolerance=tolerance, include_matches=include_matches)

    def ledger_snapshot(self, item_id=None, warehouse_id=None) -> Dict[str, Any]:
        return self.rest_client.get_inventory_ledger_snapshot(item_id=item_id, warehouse_id=warehouse_id)

    def ledger_health(self, item_id=None, warehouse_id=None, tolerance='0') -> Dict[str, Any]:
        return self.rest_client.get_inventory_ledger_health(item_id=item_id, warehouse_id=warehouse_id, tolerance=tolerance)

    def ledger_backfill(self, dry_run=True, item_id=None, warehouse_id=None, clear_existing=False,
                        include_item_movements=True, include_warehouse_movements=True) -> Dict[str, Any]:
        return self.rest_client.inventory_ledger_backfill(
            dry_run=dry_run,
            item_id=item_id,
            warehouse_id=warehouse_id,
            clear_existing=clear_existing,
            include_item_movements=include_item_movements,
            include_warehouse_movements=include_warehouse_movements,
        )

    def ledger_readiness(self, item_id=None, warehouse_id=None, tolerance='0') -> Dict[str, Any]:
        return self.rest_client.get_inventory_ledger_readiness(item_id=item_id, warehouse_id=warehouse_id, tolerance=tolerance)

    def ledger_controlled_read(self, item_id=None, warehouse_id=None, mode='operational', tolerance='0') -> Dict[str, Any]:
        return self.rest_client.get_inventory_ledger_controlled_read(item_id=item_id, warehouse_id=warehouse_id, mode=mode, tolerance=tolerance)

    def is_remote(self) -> bool:
        return True
