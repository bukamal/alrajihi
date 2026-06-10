# -*- coding: utf-8 -*-
from database.repositories.base_repo import BaseRepository
from typing import List, Dict

class InventoryMovementRepository(BaseRepository):
    def get_movements(self, item_id: int) -> List[Dict]:
        if self.db.is_remote():
            raise NotImplementedError("Use REST")
        else:
            from auth.session import UserSession
            uid = UserSession.get_current_user_id()
            return self._fetch_all("""
                SELECT movement_type, quantity, unit_cost, movement_date, reference_id
                FROM inventory_movements
                WHERE item_id = ? AND user_id = ?
                ORDER BY movement_date DESC
            """, (item_id, uid))
    
    def record_movement(self, item_id: int, movement_type: str, quantity: float, unit_cost: float, reference_id: int = None):
        if self.db.is_remote():
            raise NotImplementedError("Use REST")
        else:
            raise NotImplementedError("Use InventoryMovementDAO for local")


