# -*- coding: utf-8 -*-
"""Remote API manufacturing gateway adapter."""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from gateways.manufacturing_gateway import ManufacturingGateway


class RemoteManufacturingGateway(ManufacturingGateway):
    def __init__(self, rest_client):
        self.rest_client = rest_client

    def get_all_boms(self, limit: int | None = None, offset: int | None = None) -> Tuple[List[Dict[str, Any]], int]:
        return self.rest_client.get_boms(limit, offset)

    def get_bom(self, bom_id: int) -> Optional[Dict[str, Any]]:
        return self.rest_client.get_bom(bom_id)

    def get_bom_for_product(self, product_id: int) -> Optional[Dict[str, Any]]:
        return self.rest_client.get_bom_for_product(product_id)

    def save_bom(self, bom_data: Dict[str, Any]) -> int:
        return self.rest_client.save_bom(bom_data)

    def can_edit_bom(self, bom_id: int):
        return self.rest_client.can_edit_bom(bom_id)

    def delete_bom(self, bom_id: int):
        self.rest_client.delete_bom(bom_id)
        return True, ''

    def get_all_production_orders(self, limit: int | None = None, offset: int | None = None) -> Tuple[List[Dict[str, Any]], int]:
        return self.rest_client.get_production_orders(limit, offset)

    def get_production_order(self, order_id: int) -> Optional[Dict[str, Any]]:
        return self.rest_client.get_production_order(order_id)

    def create_production_order(self, product_id: int, planned_qty, notes: str = '', raw_warehouse_id=None, output_warehouse_id=None) -> int:
        return self.rest_client.create_production_order({
            'product_id': product_id,
            'planned_qty': str(planned_qty),
            'notes': notes,
            'raw_warehouse_id': raw_warehouse_id,
            'output_warehouse_id': output_warehouse_id,
        })

    def start_production(self, order_id: int):
        self.rest_client.start_production(order_id)
        return True, ''

    def cancel_production(self, order_id: int):
        result = self.rest_client.cancel_production(order_id)
        return (True, '') if result is None else result

    def consume_material(self, order_id: int, item_id: int, consumed_qty, unit_cost):
        self.rest_client.consume_material(order_id, item_id, consumed_qty, unit_cost)
        return True, ''

    def complete_production(self, order_id: int, produced_qty):
        self.rest_client.complete_production(order_id, produced_qty)
        return True, ''

    def delete_production_order(self, order_id: int):
        self.rest_client.delete_production_order(order_id)
        return True, ''

    def reverse_production_order(self, order_id: int):
        self.rest_client.reverse_production_order(order_id)
        return True, ''

    def get_required_materials_recursive(self, product_id: int, planned_qty, warehouse_id=None) -> List[Dict[str, Any]]:
        bom = self.get_bom_for_product(product_id)
        if not bom or not bom.get('id'):
            return []
        return self.rest_client.get_required_materials(bom['id'], planned_qty, warehouse_id=warehouse_id)

    def get_required_materials(self, *args) -> List[Dict[str, Any]]:
        return self.rest_client.get_required_materials(*args)

    def check_materials_availability(self, *args):
        if len(args) >= 2:
            return self.rest_client.check_materials_availability(args[0], args[1])
        if not args:
            return False, []
        order = self.get_production_order(args[0])
        if not order:
            return False, []
        bom = self.get_bom_for_product(order.get('product_id'))
        if not bom or not bom.get('id'):
            return False, []
        return self.rest_client.check_materials_availability(bom['id'], order.get('planned_qty'))

    def get_reservations(self, order_id: int) -> List[Dict[str, Any]]:
        return self.rest_client.get_reservations(order_id)

    def get_consumptions(self, order_id: int) -> List[Dict[str, Any]]:
        return self.rest_client.get_consumptions(order_id)

    def get_outputs(self, order_id: int) -> List[Dict[str, Any]]:
        return self.rest_client.get_outputs(order_id)

    def get_consumption(self, consumption_id: int) -> Optional[Dict[str, Any]]:
        return None

    def get_output(self, output_id: int) -> Optional[Dict[str, Any]]:
        return None

    def delete_consumption(self, consumption_id: int):
        return self.rest_client.delete_consumption(consumption_id)

    def delete_output(self, output_id: int):
        return self.rest_client.delete_output(output_id)

    def is_remote(self) -> bool:
        return True
