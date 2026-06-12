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

    def is_remote(self) -> bool:
        return True
