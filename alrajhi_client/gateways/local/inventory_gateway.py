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

    def is_remote(self) -> bool:
        return False
