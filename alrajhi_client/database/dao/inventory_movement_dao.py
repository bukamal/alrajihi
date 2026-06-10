# -*- coding: utf-8 -*-
from database.connection import DatabaseConnection
from decimal import Decimal
from auth.session import UserSession
import datetime

class InventoryMovementDAO:
    def __init__(self):
        self.db = DatabaseConnection()
    
    def get_movements(self, item_id):
        uid = UserSession.get_current_user_id()
        rows = self.db.execute("""
            SELECT movement_type, quantity, unit_cost, movement_date, reference_id
            FROM inventory_movements
            WHERE item_id = ? AND user_id = ?
            ORDER BY movement_date DESC
        """, (item_id, uid)).fetchall()
        result = []
        for row in rows:
            d = dict(row)
            d['quantity'] = Decimal(str(d['quantity'])) if d['quantity'] else Decimal('0')
            d['unit_cost'] = Decimal(str(d['unit_cost'])) if d['unit_cost'] else Decimal('0')
            result.append(d)
        return result
    
    def record_movement(self, item_id, movement_type, quantity, unit_cost, reference_id=None):
        uid = UserSession.get_current_user_id()
        if not uid:
            return
        now = datetime.datetime.now().isoformat()
        self.db.execute("""
            INSERT INTO inventory_movements (item_id, user_id, movement_type, quantity, unit_cost, reference_id, movement_date)
            VALUES (?,?,?,?,?,?,?)
        """, (item_id, uid, movement_type, str(quantity), str(unit_cost), reference_id, now))
        self.db.commit()
        self._update_item_quantity(item_id)
        self._recalculate_average_cost(item_id)
    
    def _update_item_quantity(self, item_id):
        cur = self.db.execute("""
            SELECT SUM(
                CASE 
                    WHEN movement_type IN ('opening','purchase','adjustment','production_out') 
                    THEN CAST(quantity AS REAL)
                    WHEN movement_type IN ('sale','production_consume') 
                    THEN -CAST(quantity AS REAL)
                    ELSE 0
                END
            ) as total_qty
            FROM inventory_movements
            WHERE item_id = ?
        """, (item_id,))
        row = cur.fetchone()
        new_qty = Decimal(str(row[0])) if row[0] else Decimal('0')
        self.db.execute("UPDATE items SET quantity = ? WHERE id = ?", (str(new_qty), item_id))
        self.db.commit()
    
    def _recalculate_average_cost(self, item_id):
        cur = self.db.execute("""
            SELECT 
                SUM(CAST(quantity AS REAL)) as total_qty,
                SUM(CAST(quantity AS REAL) * CAST(unit_cost AS REAL)) as total_cost
            FROM inventory_movements
            WHERE item_id = ? AND movement_type IN ('opening', 'purchase', 'adjustment', 'production_out')
        """, (item_id,))
        row = cur.fetchone()
        total_qty = Decimal(str(row[0])) if row[0] else Decimal('0')
        total_cost = Decimal(str(row[1])) if row[1] else Decimal('0')
        avg = total_cost / total_qty if total_qty > 0 else Decimal('0')
        self.db.execute("UPDATE items SET average_cost = ? WHERE id = ?", (str(avg), item_id))
        self.db.commit()




# Backward-compatible singleton for legacy imports.
inventory_dao = InventoryMovementDAO()
