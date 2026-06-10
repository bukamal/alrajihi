# -*- coding: utf-8 -*-
from database.repositories.base_repo import BaseRepository
from decimal import Decimal
from typing import List, Dict, Optional, Tuple

class CustomerRepository(BaseRepository):
    def get_all(self, search: str = None, limit: int = None, offset: int = None) -> Tuple[List[Dict], int]:
        return self.db.get_customers(search, limit, offset)
    
    def get_by_id(self, customer_id: int) -> Optional[Dict]:
        if self.db.is_remote():
            customers, _ = self.get_all()
            for c in customers:
                if c['id'] == customer_id:
                    return c
            return None
        else:
            conn = self.db.get_connection()
            row = conn.execute("SELECT * FROM customers WHERE id=?", (customer_id,)).fetchone()
            return dict(row) if row else None
    
    def add(self, name: str, phone: str = '', address: str = '') -> int:
        if self.db.is_remote():
            data = {'name': name, 'phone': phone, 'address': address}
            return self.db.get_rest_client().add_customer(data)
        else:
            from auth.session import UserSession
            uid = UserSession.get_current_user_id()
            conn = self.db.get_connection()
            cursor = conn.execute('''
                INSERT INTO customers (user_id, name, phone, address, balance)
                VALUES (?,?,?,?,?)
            ''', (uid, name, phone, address, '0'))
            conn.commit()
            return cursor.lastrowid
    
    def update(self, customer_id: int, name: str, phone: str, address: str):
        if self.db.is_remote():
            data = {'name': name, 'phone': phone, 'address': address}
            self.db.get_rest_client().update_customer(customer_id, data)
        else:
            from auth.session import UserSession
            uid = UserSession.get_current_user_id()
            conn = self.db.get_connection()
            conn.execute('''
                UPDATE customers SET name=?, phone=?, address=?
                WHERE id=? AND user_id=?
            ''', (name, phone, address, customer_id, uid))
            conn.commit()
    
    def delete(self, customer_id: int):
        if self.db.is_remote():
            self.db.get_rest_client().delete_customer(customer_id)
        else:
            from auth.session import UserSession
            uid = UserSession.get_current_user_id()
            conn = self.db.get_connection()
            conn.execute("DELETE FROM customers WHERE id=? AND user_id=?", (customer_id, uid))
            conn.commit()
    
    def update_balance(self, customer_id: int, delta: Decimal):
        if self.db.is_remote():
            raise NotImplementedError("Use REST for balance update")
        from auth.session import UserSession
        uid = UserSession.get_current_user_id()
        conn = self.db.get_connection()
        conn.execute("UPDATE customers SET balance = CAST(COALESCE(balance, '0') AS TEXT) + ? WHERE id=? AND user_id=?",
                     (str(delta), customer_id, uid))
        conn.commit()


