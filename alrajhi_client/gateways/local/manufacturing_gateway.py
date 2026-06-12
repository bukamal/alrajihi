# -*- coding: utf-8 -*-
"""Local manufacturing gateway adapter."""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from database.dao.manufacturing_dao import manufacturing_dao
from gateways.manufacturing_gateway import ManufacturingGateway


class LocalManufacturingGateway(ManufacturingGateway):
    def __init__(self):
        self.dao = manufacturing_dao

    def get_all_boms(self, limit: int | None = None, offset: int | None = None) -> Tuple[List[Dict[str, Any]], int]:
        return self.dao.get_all_boms(limit=limit, offset=offset)

    def get_bom(self, bom_id: int) -> Optional[Dict[str, Any]]:
        return self.dao.get_bom(bom_id)

    def get_bom_for_product(self, product_id: int) -> Optional[Dict[str, Any]]:
        return self.dao.get_bom_for_product(product_id)

    def save_bom(self, bom_data: Dict[str, Any]) -> int:
        return self.dao.save_bom(bom_data)

    def can_edit_bom(self, bom_id: int):
        return self.dao.can_edit_bom(bom_id)

    def delete_bom(self, bom_id: int):
        return self.dao.delete_bom(bom_id)

    def get_all_production_orders(self, limit: int | None = None, offset: int | None = None) -> Tuple[List[Dict[str, Any]], int]:
        return self.dao.get_all_production_orders(limit=limit, offset=offset)

    def get_production_order(self, order_id: int) -> Optional[Dict[str, Any]]:
        return self.dao.get_production_order(order_id)

    def create_production_order(self, product_id: int, planned_qty, notes: str = '', raw_warehouse_id=None, output_warehouse_id=None) -> int:
        return self.dao.create_production_order(product_id, planned_qty, notes, raw_warehouse_id, output_warehouse_id)

    def start_production(self, order_id: int):
        return self.dao.start_production(order_id)

    def cancel_production(self, order_id: int):
        return self.dao.cancel_production(order_id)

    def consume_material(self, order_id: int, item_id: int, consumed_qty, unit_cost):
        return self.dao.consume_material(order_id, item_id, consumed_qty, unit_cost)

    def complete_production(self, order_id: int, produced_qty):
        return self.dao.complete_production(order_id, produced_qty)

    def delete_production_order(self, order_id: int):
        return self.dao.delete_production_order(order_id)

    def reverse_production_order(self, order_id: int):
        return self.dao.reverse_production_order(order_id)

    def get_required_materials_recursive(self, product_id: int, planned_qty, warehouse_id=None) -> List[Dict[str, Any]]:
        return self.dao.get_required_materials_recursive(product_id, planned_qty, warehouse_id)

    def get_required_materials(self, *args) -> List[Dict[str, Any]]:
        return self.dao.get_required_materials(*args)

    def check_materials_availability(self, *args):
        return self.dao.check_materials_availability(*args)

    def get_reservations(self, order_id: int) -> List[Dict[str, Any]]:
        return self.dao.get_reservations(order_id)

    def get_consumptions(self, order_id: int) -> List[Dict[str, Any]]:
        return self.dao.get_consumptions(order_id)

    def get_outputs(self, order_id: int) -> List[Dict[str, Any]]:
        return self.dao.get_outputs(order_id)

    def get_consumption(self, consumption_id: int) -> Optional[Dict[str, Any]]:
        try:
            row = self.dao.db.execute('SELECT * FROM production_consumptions WHERE id=?', (consumption_id,)).fetchone()
            return dict(row) if row else None
        except Exception:
            return None

    def get_output(self, output_id: int) -> Optional[Dict[str, Any]]:
        try:
            row = self.dao.db.execute('SELECT * FROM production_outputs WHERE id=?', (output_id,)).fetchone()
            return dict(row) if row else None
        except Exception:
            return None

    def delete_consumption(self, consumption_id: int):
        return self.dao.delete_consumption(consumption_id)

    def delete_output(self, output_id: int):
        return self.dao.delete_output(output_id)

    def is_remote(self) -> bool:
        return False
