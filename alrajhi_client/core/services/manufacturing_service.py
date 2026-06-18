# -*- coding: utf-8 -*-
"""Manufacturing application service.

This service is the application boundary for manufacturing workflows.  UI code
uses this service, while local/remote persistence is selected by
ManufacturingGateway adapters.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Dict, List, Optional, Tuple

from core.compat import records, pair
from gateways.manufacturing_gateway import create_manufacturing_gateway
from core.services.audit_service import audit_service
from core.services.warehouse_service import warehouse_service
from core.services.manufacturing_operation_policy import manufacturing_operation_policy


class ManufacturingService:
    """Service facade for BOM and production workflows."""

    def __init__(self, gateway=None):
        self.gateway = gateway or create_manufacturing_gateway()

    def _require(self, operation: str, context: str = '', payload: Dict | None = None) -> None:
        manufacturing_operation_policy.require(operation, context=context, payload=payload)

    def can_operation(self, operation: str) -> bool:
        return manufacturing_operation_policy.can(operation)

    # BOM
    def boms_pair(self, limit: int | None = None, offset: int | None = None) -> Tuple[List[Dict], int]:
        self._require(manufacturing_operation_policy.OP_USE, context='boms_pair')
        return pair(self.gateway.get_all_boms(limit=limit, offset=offset), 'boms')

    def boms(self, limit: int | None = None, offset: int | None = None) -> List[Dict]:
        self._require(manufacturing_operation_policy.OP_USE, context='boms')
        return records(self.gateway.get_all_boms(limit=limit, offset=offset), 'boms')

    def get_bom(self, bom_id: int) -> Optional[Dict]:
        self._require(manufacturing_operation_policy.OP_USE, context='get_bom', payload={'bom_id': bom_id})
        bom = self.gateway.get_bom(bom_id)
        return bom if isinstance(bom, dict) else None

    def get_bom_for_product(self, product_id: int) -> Optional[Dict]:
        bom = self.gateway.get_bom_for_product(product_id)
        return bom if isinstance(bom, dict) else None

    def save_bom(self, bom_data: Dict) -> int:
        """Validate and save a bill of materials through the manufacturing boundary."""
        op = manufacturing_operation_policy.OP_BOM_EDIT if bom_data.get('id') or bom_data.get('bom_id') else manufacturing_operation_policy.OP_BOM_CREATE
        self._require(op, context='save_bom', payload={'bom_id': bom_data.get('id') or bom_data.get('bom_id')})
        bom_id = self.gateway.save_bom(bom_data)
        audit_service.log('CREATE', 'BOM', bom_id, new_values=bom_data, details='حفظ BOM')
        return bom_id

    def can_edit_bom(self, bom_id: int):
        return self.gateway.can_edit_bom(bom_id)

    def delete_bom(self, bom_id: int):
        self._require(manufacturing_operation_policy.OP_BOM_DELETE, context='delete_bom', payload={'bom_id': bom_id})
        old = self.get_bom(bom_id)
        result = self.gateway.delete_bom(bom_id)
        audit_service.log('DELETE', 'BOM', bom_id, old_values=old, details='حذف BOM')
        return result

    def warehouses(self):
        return warehouse_service.warehouses()

    def default_warehouse_id(self):
        return warehouse_service.default_warehouse_id()

    def available_qty(self, item_id: int, warehouse_id=None):
        return warehouse_service.available_qty(item_id, warehouse_id)

    # Production orders
    def production_orders_pair(self, limit: int | None = None, offset: int | None = None) -> Tuple[List[Dict], int]:
        self._require(manufacturing_operation_policy.OP_USE, context='production_orders_pair')
        return pair(self.gateway.get_all_production_orders(limit=limit, offset=offset), 'orders')

    def production_orders(self, limit: int | None = None, offset: int | None = None) -> List[Dict]:
        self._require(manufacturing_operation_policy.OP_USE, context='production_orders')
        return records(self.gateway.get_all_production_orders(limit=limit, offset=offset), 'orders')

    def get_production_order(self, order_id: int) -> Optional[Dict]:
        self._require(manufacturing_operation_policy.OP_USE, context='get_production_order', payload={'order_id': order_id})
        order = self.gateway.get_production_order(order_id)
        return order if isinstance(order, dict) else None

    def create_production_order(self, product_id: int | Dict, planned_qty=None, notes: str = '', raw_warehouse_id=None, output_warehouse_id=None) -> int:
        """Create an order using either legacy dict payload or explicit args."""
        self._require(manufacturing_operation_policy.OP_ORDER_CREATE, context='create_production_order')
        if isinstance(product_id, dict):
            data = dict(product_id)
            order_id = self.gateway.create_production_order(
                data.get('product_id'),
                Decimal(str(data.get('planned_qty', data.get('quantity', '0')))),
                data.get('notes', ''),
                data.get('raw_warehouse_id') or data.get('warehouse_id'),
                data.get('output_warehouse_id') or data.get('warehouse_id')
            )
            audit_service.log('CREATE', 'PRODUCTION_ORDER', order_id, new_values=data, details='إنشاء أمر إنتاج')
            return order_id
        order_id = self.gateway.create_production_order(product_id, Decimal(str(planned_qty)), notes, raw_warehouse_id, output_warehouse_id)
        audit_service.log('CREATE', 'PRODUCTION_ORDER', order_id, new_values={
            'product_id': product_id, 'planned_qty': str(planned_qty), 'notes': notes,
            'raw_warehouse_id': raw_warehouse_id, 'output_warehouse_id': output_warehouse_id
        }, details='إنشاء أمر إنتاج')
        return order_id

    def start_production(self, order_id: int):
        self._require(manufacturing_operation_policy.OP_ORDER_START, context='start_production', payload={'order_id': order_id})
        old = self.get_production_order(order_id)
        result = self.gateway.start_production(order_id)
        new = self.get_production_order(order_id)
        audit_service.log('POST', 'PRODUCTION_ORDER', order_id, old_values=old, new_values=new, details='بدء إنتاج')
        return result

    def cancel_production(self, order_id: int):
        self._require(manufacturing_operation_policy.OP_ORDER_CANCEL, context='cancel_production', payload={'order_id': order_id})
        old = self.get_production_order(order_id)
        result = self.gateway.cancel_production(order_id)
        new = self.get_production_order(order_id)
        audit_service.log('CANCEL', 'PRODUCTION_ORDER', order_id, old_values=old, new_values=new, details='إلغاء أمر إنتاج')
        return result

    def consume_material(self, order_id: int, item_id: int, consumed_qty, unit_cost):
        self._require(manufacturing_operation_policy.OP_MATERIAL_CONSUME, context='consume_material', payload={'order_id': order_id, 'item_id': item_id})
        result = self.gateway.consume_material(order_id, item_id, consumed_qty, unit_cost)
        audit_service.log('POST', 'PRODUCTION_ORDER', order_id, new_values={'item_id': item_id, 'consumed_qty': str(consumed_qty), 'unit_cost': str(unit_cost)}, details='استهلاك مواد إنتاج')
        return result

    def complete_production(self, order_id: int, produced_qty):
        self._require(manufacturing_operation_policy.OP_OUTPUT_COMPLETE, context='complete_production', payload={'order_id': order_id})
        old = self.get_production_order(order_id)
        result = self.gateway.complete_production(order_id, produced_qty)
        new = self.get_production_order(order_id)
        audit_service.log('POST', 'PRODUCTION_ORDER', order_id, old_values=old, new_values=new, details='إتمام إنتاج')
        return result

    def delete_production_order(self, order_id: int):
        self._require(manufacturing_operation_policy.OP_ORDER_DELETE, context='delete_production_order', payload={'order_id': order_id})
        old = self.get_production_order(order_id)
        result = self.gateway.delete_production_order(order_id)
        audit_service.log('DELETE', 'PRODUCTION_ORDER', order_id, old_values=old, details='حذف أمر إنتاج')
        return result

    def reverse_production_order(self, order_id: int):
        self._require(manufacturing_operation_policy.OP_ORDER_REVERSE, context='reverse_production_order', payload={'order_id': order_id})
        old = self.get_production_order(order_id)
        result = self.gateway.reverse_production_order(order_id)
        new = self.get_production_order(order_id)
        audit_service.log('REVERSE', 'PRODUCTION_ORDER', order_id, old_values=old, new_values=new, details='عكس أمر إنتاج')
        return result

    # Materials, reservations and outputs
    def get_required_materials_recursive(self, product_id: int, planned_qty: Decimal, warehouse_id=None) -> List[Dict]:
        return records(self.gateway.get_required_materials_recursive(product_id, planned_qty, warehouse_id), 'materials')

    def get_required_materials(self, *args) -> List[Dict]:
        return records(self.gateway.get_required_materials(*args), 'materials')

    def check_materials_availability(self, *args):
        return self.gateway.check_materials_availability(*args)

    def get_reservations(self, order_id: int) -> List[Dict]:
        return records(self.gateway.get_reservations(order_id), 'reservations')

    def get_consumptions(self, order_id: int) -> List[Dict]:
        return records(self.gateway.get_consumptions(order_id), 'consumptions')

    def get_outputs(self, order_id: int) -> List[Dict]:
        return records(self.gateway.get_outputs(order_id), 'outputs')

    def delete_consumption(self, consumption_id: int):
        self._require(manufacturing_operation_policy.OP_CONSUMPTION_DELETE, context='delete_consumption', payload={'consumption_id': consumption_id})
        old = None
        try:
            old = self.gateway.get_consumption(consumption_id)
        except Exception:
            pass
        result = self.gateway.delete_consumption(consumption_id)
        audit_service.log('DELETE', 'PRODUCTION_CONSUMPTION', consumption_id, old_values=old, details='حذف استهلاك مادة إنتاج')
        return result

    def delete_output(self, output_id: int):
        self._require(manufacturing_operation_policy.OP_OUTPUT_DELETE, context='delete_output', payload={'output_id': output_id})
        old = None
        try:
            old = self.gateway.get_output(output_id)
        except Exception:
            pass
        result = self.gateway.delete_output(output_id)
        audit_service.log('DELETE', 'PRODUCTION_OUTPUT', output_id, old_values=old, details='حذف مخرج إنتاج')
        return result


manufacturing_service = ManufacturingService()
