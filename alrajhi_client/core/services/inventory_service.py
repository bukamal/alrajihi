# -*- coding: utf-8 -*-
"""Inventory movement service.

The legacy code has both inventory_dao and inventory_movement_dao wrappers. This
service is the stable import point for new code and for repository-side inventory
posting, without deleting the old compatibility modules yet.
"""
from __future__ import annotations

from typing import Dict, List

from core.compat import records
from database.dao.inventory_movement_dao import InventoryMovementDAO


class InventoryService:
    def __init__(self):
        self.movement_dao = InventoryMovementDAO()

    def movements(self, item_id: int) -> List[Dict]:
        return records(self.movement_dao.get_movements(item_id), 'movements')

    def record_movement(self, item_id: int, movement_type: str, quantity, unit_cost, reference_id=None):
        return self.movement_dao.record_movement(item_id, movement_type, quantity, unit_cost, reference_id)


inventory_service = InventoryService()
