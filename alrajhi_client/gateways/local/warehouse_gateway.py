# -*- coding: utf-8 -*-
"""Local warehouse gateway adapter.

This is the only gateway layer allowed to use the legacy warehouse DAO.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from core.compat import records
from database.dao.warehouse_dao import warehouse_dao
from gateways.warehouse_gateway import WarehouseGateway


class LocalWarehouseGateway(WarehouseGateway):
    def bootstrap(self) -> None:
        warehouse_dao.bootstrap_defaults()

    def list(self, include_archived: bool = False) -> List[Dict[str, Any]]:
        return records(warehouse_dao.get_all(include_archived=include_archived), 'warehouses')

    def get(self, warehouse_id: int) -> Optional[Dict[str, Any]]:
        warehouse = warehouse_dao.get_by_id(warehouse_id)
        return warehouse if isinstance(warehouse, dict) else None

    def create(self, data: Dict[str, Any]) -> int:
        return warehouse_dao.add(data)

    def update(self, warehouse_id: int, data: Dict[str, Any]):
        return warehouse_dao.update(warehouse_id, data)

    def archive(self, warehouse_id: int):
        return warehouse_dao.delete(warehouse_id)

    def balances(self, search: str | None = None, warehouse_id: int | None = None,
                 limit: int | None = None, offset: int | None = None) -> List[Dict[str, Any]]:
        return records(warehouse_dao.balances(search=search, warehouse_id=warehouse_id, limit=limit, offset=offset), 'balances')

    def balance_count(self, search: str | None = None, warehouse_id: int | None = None) -> int:
        return int(warehouse_dao.balance_count(search=search, warehouse_id=warehouse_id) or 0)

    def movements(self, item_id: int | None = None, warehouse_id: int | None = None,
                  limit: int = 100) -> List[Dict[str, Any]]:
        return records(warehouse_dao.movements(item_id=item_id, warehouse_id=warehouse_id, limit=limit), 'movements')

    def default_warehouse_id(self) -> int | None:
        return warehouse_dao.default_warehouse_id()

    def default_warehouse(self) -> Optional[Dict[str, Any]]:
        warehouse = warehouse_dao.default_warehouse()
        return warehouse if isinstance(warehouse, dict) else None

    def available_qty(self, item_id: int, warehouse_id: int | None = None, variant_id: int | None = None):
        return warehouse_dao.available_qty(item_id, warehouse_id, variant_id=variant_id)

    def record_movement(self, item_id, warehouse_id, movement_type, quantity,
                        unit_cost='0', reference_type=None, reference_id=None, notes='', **variant_data):
        return warehouse_dao.record_movement(item_id, warehouse_id, movement_type, quantity, unit_cost, reference_type, reference_id, notes, **variant_data)

    def reverse_reference(self, reference_type, reference_id) -> None:
        warehouse_dao.reverse_reference(reference_type, reference_id)

    def transfers(self, limit: int = 200) -> List[Dict[str, Any]]:
        return records(warehouse_dao.transfers(limit=limit), 'transfers')

    def create_transfer(self, data: Dict[str, Any]) -> int:
        return warehouse_dao.create_transfer(data)

    def cancel_transfer(self, transfer_id: int):
        return warehouse_dao.cancel_transfer(transfer_id)

    def is_remote(self) -> bool:
        return False
