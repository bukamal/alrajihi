# -*- coding: utf-8 -*-
from database.repositories.base_repo import BaseRepository
from decimal import Decimal
from typing import List, Dict, Optional

class ManufacturingRepository(BaseRepository):
    def get_all_boms(self) -> List[Dict]:
        if self.db.is_remote():
            return self.db.get_rest_client().get_boms()
        else:
            from auth.session import UserSession
            uid = UserSession.get_current_user_id()
            rows = self._fetch_all("""
                SELECT b.*, i.name as product_name 
                FROM bom b
                JOIN items i ON b.product_id = i.id
                WHERE b.user_id = ?
                ORDER BY b.id DESC
            """, (uid,))
            return rows
    
    def get_bom(self, bom_id: int) -> Optional[Dict]:
        if self.db.is_remote():
            return self.db.get_rest_client().get_bom(bom_id)
        else:
            from auth.session import UserSession
            uid = UserSession.get_current_user_id()
            row = self._fetch_one("""
                SELECT b.*, i.name as product_name 
                FROM bom b
                JOIN items i ON b.product_id = i.id
                WHERE b.id = ? AND b.user_id = ?
            """, (bom_id, uid))
            if row:
                lines = self._fetch_all("""
                    SELECT bl.*, i.name as item_name, u.unit_name
                    FROM bom_lines bl
                    JOIN items i ON bl.item_id = i.id
                    LEFT JOIN item_units u ON bl.unit_id = u.id
                    WHERE bl.bom_id = ?
                """, (bom_id,))
                row['lines'] = lines
            return row
    
    def get_bom_for_product(self, product_id: int) -> Optional[Dict]:
        if self.db.is_remote():
            boms = self.get_all_boms()
            for b in boms:
                if b['product_id'] == product_id:
                    return self.get_bom(b['id'])
            return None
        else:
            from auth.session import UserSession
            uid = UserSession.get_current_user_id()
            row = self._fetch_one("""
                SELECT id FROM bom WHERE product_id = ? AND user_id = ?
            """, (product_id, uid))
            if row:
                return self.get_bom(row['id'])
            return None
    
    def save_bom(self, bom_data: Dict) -> int:
        if self.db.is_remote():
            return self.db.get_rest_client().save_bom(bom_data)
        else:
            from auth.session import UserSession
            uid = UserSession.get_current_user_id()
            now = __import__('datetime').datetime.now().isoformat()
            if bom_data.get('id'):
                self._execute("""
                    UPDATE bom SET product_id=?, quantity=?, updated_at=?
                    WHERE id=? AND user_id=?
                """, (bom_data['product_id'], str(bom_data['quantity']), now, bom_data['id'], uid))
                self._execute("DELETE FROM bom_lines WHERE bom_id=?", (bom_data['id'],))
                bom_id = bom_data['id']
            else:
                cur = self._execute("""
                    INSERT INTO bom (product_id, quantity, user_id, created_at, updated_at)
                    VALUES (?,?,?,?,?)
                """, (bom_data['product_id'], str(bom_data['quantity']), uid, now, now))
                bom_id = cur.lastrowid
            for line in bom_data.get('lines', []):
                self._execute("""
                    INSERT INTO bom_lines (bom_id, item_id, quantity, unit_id, waste_percent)
                    VALUES (?,?,?,?,?)
                """, (bom_id, line['item_id'], str(line['quantity']), line.get('unit_id'), str(line.get('waste_percent', 0))))
            self._commit()
            return bom_id
    
    def delete_bom(self, bom_id: int) -> bool:
        if self.db.is_remote():
            self.db.get_rest_client().delete_bom(bom_id)
            return True
        else:
            from auth.session import UserSession
            uid = UserSession.get_current_user_id()
            self._execute("DELETE FROM bom WHERE id=? AND user_id=?", (bom_id, uid))
            self._commit()
            return True
    
    def get_all_production_orders(self) -> List[Dict]:
        if self.db.is_remote():
            return self.db.get_rest_client().get_production_orders()
        else:
            from auth.session import UserSession
            uid = UserSession.get_current_user_id()
            rows = self._fetch_all("""
                SELECT po.*, i.name as product_name 
                FROM production_orders po
                JOIN items i ON po.product_id = i.id
                WHERE po.user_id = ?
                ORDER BY po.id DESC
            """, (uid,))
            return rows
    
    def get_production_order(self, order_id: int) -> Optional[Dict]:
        if self.db.is_remote():
            orders = self.get_all_production_orders()
            for o in orders:
                if o['id'] == order_id:
                    return o
            return None
        else:
            row = self._fetch_one("SELECT * FROM production_orders WHERE id=?", (order_id,))
            if row:
                consumptions = self._fetch_all("SELECT * FROM production_consumptions WHERE order_id=?", (order_id,))
                outputs = self._fetch_all("SELECT * FROM production_outputs WHERE order_id=?", (order_id,))
                row['consumptions'] = consumptions
                row['outputs'] = outputs
            return row
    
    def create_production_order(self, product_id: int, planned_qty: float, notes: str = '') -> int:
        if self.db.is_remote():
            data = {'product_id': product_id, 'planned_qty': planned_qty, 'notes': notes}
            return self.db.get_rest_client().create_production_order(data)
        else:
            from auth.session import UserSession
            uid = UserSession.get_current_user_id()
            now = __import__('datetime').datetime.now().isoformat()
            year = __import__('datetime').datetime.now().strftime("%Y%m%d")
            cur = self._execute("SELECT order_number FROM production_orders ORDER BY id DESC LIMIT 1")
            last = cur.fetchone()
            if last:
                parts = last['order_number'].split('-')
                if len(parts) == 2 and parts[0] == year:
                    num = int(parts[1]) + 1
                else:
                    num = 1
            else:
                num = 1
            order_number = f"{year}-{num:04d}"
            bom = self.get_bom_for_product(product_id)
            snapshot_id = None
            if bom:
                cur = self._execute("""
                    INSERT INTO bom_snapshots (order_number, product_id, product_name, created_at)
                    VALUES (?,?,?,?)
                """, (order_number, product_id, bom.get('product_name', ''), now))
                snapshot_id = cur.lastrowid
                for line in bom.get('lines', []):
                    self._execute("""
                        INSERT INTO bom_snapshot_lines (snapshot_id, item_id, item_name, quantity, unit_name, conversion_factor, waste_percent)
                        VALUES (?,?,?,?,?,?,?)
                    """, (snapshot_id, line['item_id'], line.get('item_name', ''), str(line['quantity']), line.get('unit_name', ''), '1', str(line.get('waste_percent', 0))))
            cur = self._execute("""
                INSERT INTO production_orders (order_number, product_id, planned_qty, status, user_id, created_at, notes, bom_snapshot_id)
                VALUES (?,?,?,?,?,?,?,?)
            """, (order_number, product_id, str(planned_qty), 'planned', uid, now, notes, snapshot_id))
            self._commit()
            return cur.lastrowid
    
    def start_production(self, order_id: int) -> bool:
        if self.db.is_remote():
            self.db.get_rest_client().start_production(order_id)
            return True
        else:
            now = __import__('datetime').datetime.now().isoformat()
            self._execute("UPDATE production_orders SET status='in_progress', start_date=? WHERE id=?", (now, order_id))
            self._commit()
            return True
    
    def complete_production(self, order_id: int, produced_qty: float) -> bool:
        if self.db.is_remote():
            self.db.get_rest_client().complete_production(order_id, produced_qty)
            return True
        else:
            now = __import__('datetime').datetime.now().isoformat()
            cons = self._fetch_all("SELECT consumed_qty, unit_cost FROM production_consumptions WHERE order_id=?", (order_id,))
            total_cost = sum(float(c['consumed_qty']) * float(c['unit_cost']) for c in cons)
            unit_cost = total_cost / produced_qty if produced_qty > 0 else 0
            order = self.get_production_order(order_id)
            if order:
                self._execute("""
                    INSERT INTO production_outputs (order_id, item_id, produced_qty, unit_cost, output_date)
                    VALUES (?,?,?,?,?)
                """, (order_id, order['product_id'], str(produced_qty), str(unit_cost), now))
                from core.services.inventory_service import inventory_service
                inventory_service.record_movement(order['product_id'], 'production_out', produced_qty, unit_cost, order_id)
            self._execute("""
                UPDATE production_orders SET produced_qty=?, status='completed', end_date=?
                WHERE id=?
            """, (str(produced_qty), now, order_id))
            self._commit()
            return True
    
    def consume_material(self, order_id: int, item_id: int, consumed_qty: float, unit_cost: float) -> bool:
        if self.db.is_remote():
            self.db.get_rest_client().consume_material(order_id, item_id, consumed_qty, unit_cost)
            return True
        else:
            now = __import__('datetime').datetime.now().isoformat()
            self._execute("""
                INSERT INTO production_consumptions (order_id, item_id, consumed_qty, unit_cost, movement_date)
                VALUES (?,?,?,?,?)
            """, (order_id, item_id, str(consumed_qty), str(unit_cost), now))
            from core.services.inventory_service import inventory_service
            inventory_service.record_movement(item_id, 'production_consume', consumed_qty, unit_cost, order_id)
            self._commit()
            return True
    
    def get_consumptions(self, order_id: int) -> List[Dict]:
        if self.db.is_remote():
            return []
        else:
            rows = self._fetch_all("SELECT * FROM production_consumptions WHERE order_id=?", (order_id,))
            return rows
    
    def get_outputs(self, order_id: int) -> List[Dict]:
        if self.db.is_remote():
            return []
        else:
            return self._fetch_all("SELECT * FROM production_outputs WHERE order_id=?", (order_id,))
    
    def delete_production_order(self, order_id: int) -> bool:
        if self.db.is_remote():
            self.db.get_rest_client().delete_production_order(order_id)
            return True
        else:
            self._execute("DELETE FROM production_consumptions WHERE order_id=?", (order_id,))
            self._execute("DELETE FROM production_outputs WHERE order_id=?", (order_id,))
            self._execute("DELETE FROM production_orders WHERE id=?", (order_id,))
            self._commit()
            return True
    
    def delete_consumption(self, consumption_id: int) -> bool:
        if self.db.is_remote():
            return False
        else:
            row = self._fetch_one("SELECT * FROM production_consumptions WHERE id=?", (consumption_id,))
            if row:
                from core.services.inventory_service import inventory_service
                inventory_service.record_movement(row['item_id'], 'adjustment', float(row['consumed_qty']), float(row['unit_cost']), None)
                self._execute("DELETE FROM production_consumptions WHERE id=?", (consumption_id,))
                self._commit()
                return True
            return False
    
    def delete_output(self, output_id: int) -> bool:
        if self.db.is_remote():
            return False
        else:
            row = self._fetch_one("SELECT * FROM production_outputs WHERE id=?", (output_id,))
            if row:
                from core.services.inventory_service import inventory_service
                inventory_service.record_movement(row['item_id'], 'adjustment', -float(row['produced_qty']), float(row['unit_cost']), None)
                self._execute("DELETE FROM production_outputs WHERE id=?", (output_id,))
                order = self._fetch_one("SELECT produced_qty FROM production_orders WHERE id=?", (row['order_id'],))
                if order:
                    new_qty = float(order['produced_qty']) - float(row['produced_qty'])
                    self._execute("UPDATE production_orders SET produced_qty=? WHERE id=?", (str(new_qty), row['order_id']))
                self._commit()
                return True
            return False
    
    def reverse_production_order(self, order_id: int) -> bool:
        if self.db.is_remote():
            return False
        else:
            consumptions = self.get_consumptions(order_id)
            for c in consumptions:
                from core.services.inventory_service import inventory_service
                inventory_service.record_movement(c['item_id'], 'adjustment', float(c['consumed_qty']), float(c['unit_cost']), None)
            outputs = self.get_outputs(order_id)
            for o in outputs:
                from core.services.inventory_service import inventory_service
                inventory_service.record_movement(o['item_id'], 'adjustment', -float(o['produced_qty']), float(o['unit_cost']), None)
            self._execute("DELETE FROM production_consumptions WHERE order_id=?", (order_id,))
            self._execute("DELETE FROM production_outputs WHERE order_id=?", (order_id,))
            self._execute("DELETE FROM production_orders WHERE id=?", (order_id,))
            self._commit()
            return True
    
    def check_materials_availability(self, bom_id: int, planned_qty: float):
        bom = self.get_bom(bom_id)
        if not bom:
            return False, []
        from database import item_dao
        required = []
        all_sufficient = True
        for line in bom.get('lines', []):
            item = item_dao.get_by_id(line['item_id'])
            qty_needed = float(line['quantity']) * planned_qty * (1 + float(line.get('waste_percent', 0)))
            available = item['available'] if item else 0
            sufficient = available >= qty_needed
            required.append({
                'item_id': line['item_id'],
                'item_name': line.get('item_name', ''),
                'required_qty': qty_needed,
                'available_qty': available,
                'is_sufficient': sufficient
            })
            if not sufficient:
                all_sufficient = False
        return all_sufficient, required
    
    def get_required_materials(self, bom_id: int, planned_qty: float):
        _, materials = self.check_materials_availability(bom_id, planned_qty)
        return materials
    
    def can_edit_bom(self, bom_id: int):
        bom = self.get_bom(bom_id)
        if not bom:
            return False, "BOM غير موجود"
        orders = self._fetch_all("""
            SELECT id, status FROM production_orders 
            WHERE product_id = ? AND status IN ('planned', 'in_progress')
        """, (bom['product_id'],))
        if orders:
            return False, f"لا يمكن تعديل BOM لوجود أوامر إنتاج نشطة: {', '.join(str(o['id']) for o in orders)}"
        return True, ""


