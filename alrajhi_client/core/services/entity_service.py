# -*- coding: utf-8 -*-
"""Customer and supplier service.

This service centralizes customer/supplier CRUD for UI code. It preserves the
legacy DAO behavior while giving widgets a stable (records, total) contract and
clean dict records.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from core.compat import pair
from database.dao.customer_dao import customer_dao
from database.dao.supplier_dao import supplier_dao
from core.services.audit_service import audit_service


class EntityService:
    def customers(self, search: str | None = None, limit: int | None = None,
                  offset: int | None = None) -> Tuple[List[Dict], int]:
        return pair(customer_dao.get_all(search=search, limit=limit, offset=offset), 'customers')

    def suppliers(self, search: str | None = None, limit: int | None = None,
                  offset: int | None = None) -> Tuple[List[Dict], int]:
        return pair(supplier_dao.get_all(search=search, limit=limit, offset=offset), 'suppliers')

    def customer_by_id(self, customer_id: int) -> Optional[Dict]:
        customer = customer_dao.get_by_id(customer_id)
        return customer if isinstance(customer, dict) else None

    def supplier_by_id(self, supplier_id: int) -> Optional[Dict]:
        supplier = supplier_dao.get_by_id(supplier_id)
        return supplier if isinstance(supplier, dict) else None

    def add_customer(self, name: str, phone: str = '', address: str = ''):
        cid = customer_dao.add(name, phone, address)
        audit_service.log('CREATE', 'CUSTOMER', cid, new_values={'name': name, 'phone': phone, 'address': address}, details='إنشاء عميل')
        return cid

    def add_supplier(self, name: str, phone: str = '', address: str = ''):
        sid = supplier_dao.add(name, phone, address)
        audit_service.log('CREATE', 'SUPPLIER', sid, new_values={'name': name, 'phone': phone, 'address': address}, details='إنشاء مورد')
        return sid

    def update_customer(self, customer_id: int, name: str, phone: str = '', address: str = ''):
        old = self.customer_by_id(customer_id)
        result = customer_dao.update(customer_id, name, phone, address)
        new = self.customer_by_id(customer_id)
        audit_service.log('UPDATE', 'CUSTOMER', customer_id, old_values=old, new_values=new, details='تعديل عميل')
        return result

    def update_supplier(self, supplier_id: int, name: str, phone: str = '', address: str = ''):
        old = self.supplier_by_id(supplier_id)
        result = supplier_dao.update(supplier_id, name, phone, address)
        new = self.supplier_by_id(supplier_id)
        audit_service.log('UPDATE', 'SUPPLIER', supplier_id, old_values=old, new_values=new, details='تعديل مورد')
        return result

    def delete_customer(self, customer_id: int):
        old = self.customer_by_id(customer_id)
        result = customer_dao.delete(customer_id)
        audit_service.log('DELETE', 'CUSTOMER', customer_id, old_values=old, details='حذف عميل')
        return result

    def delete_supplier(self, supplier_id: int):
        old = self.supplier_by_id(supplier_id)
        result = supplier_dao.delete(supplier_id)
        audit_service.log('DELETE', 'SUPPLIER', supplier_id, old_values=old, details='حذف مورد')
        return result


entity_service = EntityService()
