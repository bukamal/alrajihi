# -*- coding: utf-8 -*-
"""Manufacturing gateway contract and factory.

This boundary removes direct ManufacturingDAO usage from application services.
Local mode delegates to the legacy DAO; remote mode delegates to the REST client.
It intentionally preserves the existing manufacturing behavior and does not
change BOM, production, stock, costing, or reversal rules.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple


class ManufacturingGateway(ABC):
    # BOM
    @abstractmethod
    def get_all_boms(self, limit: int | None = None, offset: int | None = None) -> Tuple[List[Dict[str, Any]], int]:
        raise NotImplementedError

    @abstractmethod
    def get_bom(self, bom_id: int) -> Optional[Dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def get_bom_for_product(self, product_id: int) -> Optional[Dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def save_bom(self, bom_data: Dict[str, Any]) -> int:
        raise NotImplementedError

    @abstractmethod
    def can_edit_bom(self, bom_id: int):
        raise NotImplementedError

    @abstractmethod
    def delete_bom(self, bom_id: int):
        raise NotImplementedError

    # Production orders
    @abstractmethod
    def get_all_production_orders(self, limit: int | None = None, offset: int | None = None) -> Tuple[List[Dict[str, Any]], int]:
        raise NotImplementedError

    @abstractmethod
    def get_production_order(self, order_id: int) -> Optional[Dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def create_production_order(self, product_id: int, planned_qty, notes: str = '', raw_warehouse_id=None, output_warehouse_id=None) -> int:
        raise NotImplementedError

    @abstractmethod
    def start_production(self, order_id: int):
        raise NotImplementedError

    @abstractmethod
    def cancel_production(self, order_id: int):
        raise NotImplementedError

    @abstractmethod
    def consume_material(self, order_id: int, item_id: int, consumed_qty, unit_cost):
        raise NotImplementedError

    @abstractmethod
    def complete_production(self, order_id: int, produced_qty):
        raise NotImplementedError

    @abstractmethod
    def delete_production_order(self, order_id: int):
        raise NotImplementedError

    @abstractmethod
    def reverse_production_order(self, order_id: int):
        raise NotImplementedError

    # Materials, reservations and outputs
    @abstractmethod
    def get_required_materials_recursive(self, product_id: int, planned_qty, warehouse_id=None) -> List[Dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def get_required_materials(self, *args) -> List[Dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def check_materials_availability(self, *args):
        raise NotImplementedError

    @abstractmethod
    def get_reservations(self, order_id: int) -> List[Dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def get_consumptions(self, order_id: int) -> List[Dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def get_outputs(self, order_id: int) -> List[Dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def get_consumption(self, consumption_id: int) -> Optional[Dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def get_output(self, output_id: int) -> Optional[Dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def delete_consumption(self, consumption_id: int):
        raise NotImplementedError

    @abstractmethod
    def delete_output(self, output_id: int):
        raise NotImplementedError

    @abstractmethod
    def is_remote(self) -> bool:
        raise NotImplementedError


def create_manufacturing_gateway() -> ManufacturingGateway:
    """Return the active manufacturing gateway for local or remote mode."""
    from database.connection import DatabaseConnection

    db = DatabaseConnection()
    if db.is_remote():
        from gateways.remote.manufacturing_gateway import RemoteManufacturingGateway
        return RemoteManufacturingGateway(db.get_rest_client())

    from gateways.local.manufacturing_gateway import LocalManufacturingGateway
    return LocalManufacturingGateway()
