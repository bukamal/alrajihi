# -*- coding: utf-8 -*-
from database.repositories.base_repo import BaseRepository
from decimal import Decimal
from typing import List, Dict, Optional, Tuple

class SupplierRepository(BaseRepository):
    def get_all(self, search: str = None, limit: int = None, offset: int = None) -> Tuple[List[Dict], int]:
        return self.db.get_suppliers(search, limit, offset)
    
    def get_by_id(self, supplier_id: int) -> Optional[Dict]:
        if self.db.is_remote():
            suppliers, _ = self.get_all()
            for s in suppliers:
                if s['id'] == supplier_id:
                    return s
            return None
        else:
            conn = self.db.get_connection()
            row = conn.execute("SELECT * FROM suppliers WHERE id=?", (supplier_id,)).fetchone()
            return dict(row) if row else None
    
    def add(self, name: str, phone: str = '', address: str = '') -> int:
        if self.db.is_remote():
            data = {'name': name, 'phone': phone, 'address': address}
            return self.db.get_rest_client().add_supplier(data)
        else:
            from auth.session import UserSession
            uid = UserSession.get_current_user_id()
            conn = self.db.get_connection()
            cursor = conn.execute('''
                INSERT INTO suppliers (user_id, name, phone, address, balance)
                VALUES (?,?,?,?,?)
            ''', (uid, name, phone, address, '0'))
            conn.commit()
            return cursor.lastrowid
    
    def update(self, supplier_id: int, name: str, phone: str, address: str):
        if self.db.is_remote():
            data = {'name': name, 'phone': phone, 'address': address}
            self.db.get_rest_client().update_supplier(supplier_id, data)
        else:
            from auth.session import UserSession
            uid = UserSession.get_current_user_id()
            conn = self.db.get_connection()
            conn.execute('''
                UPDATE suppliers SET name=?, phone=?, address=?
                WHERE id=? AND user_id=?
            ''', (name, phone, address, supplier_id, uid))
            conn.commit()
    
    def delete(self, supplier_id: int):
        if self.db.is_remote():
            self.db.get_rest_client().delete_supplier(supplier_id)
        else:
            from auth.session import UserSession
            uid = UserSession.get_current_user_id()
            conn = self.db.get_connection()
            conn.execute("DELETE FROM suppliers WHERE id=? AND user_id=?", (supplier_id, uid))
            conn.commit()
    
    def update_balance(self, supplier_id: int, delta: Decimal):
        if self.db.is_remote():
            raise NotImplementedError("Use REST for balance update")
        from auth.session import UserSession
        uid = UserSession.get_current_user_id()
        conn = self.db.get_connection()
        conn.execute("UPDATE suppliers SET balance = CAST(COALESCE(balance, '0') AS TEXT) + ? WHERE id=? AND user_id=?",
                     (str(delta), supplier_id, uid))
        conn.commit()


