# -*- coding: utf-8 -*-
"""Inventory movement service.

The legacy code has both inventory_dao and inventory_movement_dao wrappers. This
service is the stable import point for new code and for repository-side inventory
posting, without deleting the old compatibility modules yet.
"""
from __future__ import annotations

from typing import Dict, List

from core.compat import records
from gateways.inventory_gateway import create_inventory_gateway
from core.services.audit_service import audit_service


class InventoryService:
    def __init__(self):
        self.gateway = create_inventory_gateway()

    def movements(self, item_id: int) -> List[Dict]:
        return records(self.gateway.movements(item_id), 'movements')

    def ledger_entries(self, **filters) -> List[Dict]:
        return records(self.gateway.ledger_entries(**filters), 'ledger')

    def record_ledger_entry(self, **data):
        entry_id = self.gateway.record_ledger_entry(data)
        audit_service.log(
            'POST', 'INVENTORY_LEDGER', entry_id,
            new_values=data,
            details='تسجيل قيد دفتر مخزون'
        )
        return entry_id

    def ledger_balance(self, item_id: int, warehouse_id=None):
        return self.gateway.ledger_balance(item_id, warehouse_id)

    def record_movement(self, item_id: int, movement_type: str, quantity, unit_cost, reference_id=None):
        movement_id = self.gateway.record_movement(item_id, movement_type, quantity, unit_cost, reference_id)
        audit_service.log(
            'POST', 'INVENTORY_MOVEMENT', movement_id,
            new_values={
                'item_id': item_id, 'movement_type': movement_type,
                'quantity': str(quantity), 'unit_cost': str(unit_cost),
                'reference_id': reference_id
            },
            details='تسجيل حركة مخزون'
        )
        return movement_id


inventory_service = InventoryService()
