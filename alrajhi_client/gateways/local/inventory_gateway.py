# -*- coding: utf-8 -*-
"""Local inventory movement gateway adapter."""
from __future__ import annotations

from typing import Any, Dict, List

from core.compat import records
from database.dao.inventory_movement_dao import InventoryMovementDAO
from database.dao.inventory_ledger_dao import InventoryLedgerDAO
from gateways.inventory_gateway import InventoryGateway


class LocalInventoryGateway(InventoryGateway):
    def __init__(self):
        self.movement_dao = InventoryMovementDAO()
        self.ledger_dao = InventoryLedgerDAO()

    def movements(self, item_id: int) -> List[Dict[str, Any]]:
        return records(self.movement_dao.get_movements(item_id), 'movements')

    def record_movement(self, item_id: int, movement_type: str, quantity,
                        unit_cost, reference_id=None) -> int | None:
        return self.movement_dao.record_movement(item_id, movement_type, quantity, unit_cost, reference_id)

    def ledger_entries(self, **filters) -> List[Dict[str, Any]]:
        return records(self.ledger_dao.list_entries(**filters), 'ledger')

    def record_ledger_entry(self, data: Dict[str, Any]) -> int | None:
        return self.ledger_dao.record_entry(**data)

    def ledger_balance(self, item_id: int, warehouse_id=None):
        return self.ledger_dao.item_balance_from_ledger(item_id, warehouse_id)

    def ledger_reconciliation(self, item_id=None, warehouse_id=None, tolerance='0') -> Dict[str, Any]:
        return self.ledger_dao.reconciliation_report(item_id=item_id, warehouse_id=warehouse_id, tolerance=tolerance)

    def ledger_dual_read(self, item_id=None, warehouse_id=None, tolerance='0', include_matches=True) -> Dict[str, Any]:
        return self.ledger_dao.dual_read_report(item_id=item_id, warehouse_id=warehouse_id, tolerance=tolerance, include_matches=include_matches)

    def ledger_snapshot(self, item_id=None, warehouse_id=None) -> Dict[str, Any]:
        return self.ledger_dao.snapshot_balance(item_id=item_id, warehouse_id=warehouse_id)

    def ledger_health(self, item_id=None, warehouse_id=None, tolerance='0') -> Dict[str, Any]:
        return self.ledger_dao.health_report(item_id=item_id, warehouse_id=warehouse_id, tolerance=tolerance)

    def ledger_backfill(self, dry_run=True, item_id=None, warehouse_id=None, clear_existing=False,
                        include_item_movements=True, include_warehouse_movements=True) -> Dict[str, Any]:
        return self.ledger_dao.backfill_ledger(
            dry_run=dry_run,
            item_id=item_id,
            warehouse_id=warehouse_id,
            clear_existing=clear_existing,
            include_item_movements=include_item_movements,
            include_warehouse_movements=include_warehouse_movements,
        )

    def ledger_readiness(self, item_id=None, warehouse_id=None, tolerance='0') -> Dict[str, Any]:
        return self.ledger_dao.readiness_gate(item_id=item_id, warehouse_id=warehouse_id, tolerance=tolerance)

    def ledger_controlled_read(self, item_id=None, warehouse_id=None, mode='operational', tolerance='0') -> Dict[str, Any]:
        return self.ledger_dao.controlled_read_balance(item_id=item_id, warehouse_id=warehouse_id, mode=mode, tolerance=tolerance)

    def is_remote(self) -> bool:
        return False
