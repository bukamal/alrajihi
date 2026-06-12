# -*- coding: utf-8 -*-
"""Remote API warehouse gateway adapter."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from gateways.warehouse_gateway import WarehouseGateway


class RemoteWarehouseGateway(WarehouseGateway):
    def __init__(self, rest_client):
        self.rest_client = rest_client

    def bootstrap(self) -> None:
        # The server endpoint ensures/defaults warehouse state on reads.
        return None

    def list(self, include_archived: bool = False) -> List[Dict[str, Any]]:
        return self.rest_client.get_warehouses(include_archived=include_archived)

    def get(self, warehouse_id: int) -> Optional[Dict[str, Any]]:
        warehouse = self.rest_client.get_warehouse(warehouse_id)
        return warehouse if isinstance(warehouse, dict) else None

    def create(self, data: Dict[str, Any]) -> int:
        return self.rest_client.add_warehouse(data)

    def update(self, warehouse_id: int, data: Dict[str, Any]):
        return self.rest_client.update_warehouse(warehouse_id, data)

    def archive(self, warehouse_id: int):
        return self.rest_client.archive_warehouse(warehouse_id)

    def balances(self, search: str | None = None, warehouse_id: int | None = None,
                 limit: int | None = None, offset: int | None = None) -> List[Dict[str, Any]]:
        return self.rest_client.get_warehouse_balances(search=search, warehouse_id=warehouse_id, limit=limit, offset=offset)

    def balance_count(self, search: str | None = None, warehouse_id: int | None = None) -> int:
        return int(self.rest_client.get_warehouse_balance_count(search=search, warehouse_id=warehouse_id) or 0)

    def movements(self, item_id: int | None = None, warehouse_id: int | None = None,
                  limit: int = 100) -> List[Dict[str, Any]]:
        return self.rest_client.get_warehouse_movements(item_id=item_id, warehouse_id=warehouse_id, limit=limit)

    def default_warehouse_id(self) -> int | None:
        return self.rest_client.default_warehouse_id()

    def default_warehouse(self) -> Optional[Dict[str, Any]]:
        wh_id = self.default_warehouse_id()
        return self.get(wh_id) if wh_id else None

    def available_qty(self, item_id: int, warehouse_id: int | None = None):
        return self.rest_client.warehouse_available_qty(item_id, warehouse_id)

    def record_movement(self, item_id, warehouse_id, movement_type, quantity,
                        unit_cost='0', reference_type=None, reference_id=None, notes=''):
        return self.rest_client.warehouse_record_movement({
            'item_id': item_id,
            'warehouse_id': warehouse_id,
            'movement_type': movement_type,
            'quantity': quantity,
            'unit_cost': unit_cost,
            'reference_type': reference_type,
            'reference_id': reference_id,
            'notes': notes,
        })

    def reverse_reference(self, reference_type, reference_id) -> None:
        self.rest_client.warehouse_reverse_reference(reference_type, reference_id)

    def transfers(self, limit: int = 200) -> List[Dict[str, Any]]:
        return self.rest_client.get_warehouse_transfers(limit=limit)

    def create_transfer(self, data: Dict[str, Any]) -> int:
        return self.rest_client.create_warehouse_transfer(data)

    def cancel_transfer(self, transfer_id: int):
        return self.rest_client.cancel_warehouse_transfer(transfer_id)

    def is_remote(self) -> bool:
        return True
