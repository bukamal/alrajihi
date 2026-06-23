# -*- coding: utf-8 -*-
from database.dao.inventory_movement_dao import InventoryMovementDAO

# واجهة توافق قديمة فوق InventoryMovementDAO.
class InventoryDAO:
    def __init__(self):
        self.movement_dao = InventoryMovementDAO()
    
    def get_movements(self, item_id):
        return self.movement_dao.get_movements(item_id)

# إنشاء كائن مفرد
inventory_dao = InventoryDAO()


