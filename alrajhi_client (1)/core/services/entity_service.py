# -*- coding: utf-8 -*-
"""Customer and supplier service.

This service centralizes customer/supplier CRUD for UI code. It preserves the
legacy DAO behavior while giving widgets a stable (records, total) contract and
clean dict records.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from gateways.entity_gateway import create_entity_gateways
from core.services.audit_service import audit_service


def _party_policy():
    from core.services.party_operation_policy import party_operation_policy
    return party_operation_policy


class EntityService:
    def __init__(self):
        self.customer_gateway, self.supplier_gateway = create_entity_gateways()

    def customers(self, search: str | None = None, limit: int | None = None,
                  offset: int | None = None) -> Tuple[List[Dict], int]:
        _party_policy().require(_party_policy().OP_CUSTOMER_VIEW, context='customers')
        return self.customer_gateway.list(search=search, limit=limit, offset=offset)

    def suppliers(self, search: str | None = None, limit: int | None = None,
                  offset: int | None = None) -> Tuple[List[Dict], int]:
        _party_policy().require(_party_policy().OP_SUPPLIER_VIEW, context='suppliers')
        return self.supplier_gateway.list(search=search, limit=limit, offset=offset)

    def customer_by_id(self, customer_id: int) -> Optional[Dict]:
        _party_policy().require(_party_policy().OP_CUSTOMER_VIEW, context='customer_by_id', payload={'id': customer_id})
        customer = self.customer_gateway.get(customer_id)
        return customer if isinstance(customer, dict) else None

    def supplier_by_id(self, supplier_id: int) -> Optional[Dict]:
        _party_policy().require(_party_policy().OP_SUPPLIER_VIEW, context='supplier_by_id', payload={'id': supplier_id})
        supplier = self.supplier_gateway.get(supplier_id)
        return supplier if isinstance(supplier, dict) else None

    def add_customer(self, name: str, phone: str = '', address: str = ''):
        _party_policy().require(_party_policy().OP_CUSTOMER_CREATE, context='add_customer', payload={'name': name})
        cid = self.customer_gateway.create({'name': name, 'phone': phone, 'address': address})
        audit_service.log('CREATE', 'CUSTOMER', cid, new_values={'name': name, 'phone': phone, 'address': address}, details='إنشاء عميل')
        return cid

    def add_supplier(self, name: str, phone: str = '', address: str = ''):
        _party_policy().require(_party_policy().OP_SUPPLIER_CREATE, context='add_supplier', payload={'name': name})
        sid = self.supplier_gateway.create({'name': name, 'phone': phone, 'address': address})
        audit_service.log('CREATE', 'SUPPLIER', sid, new_values={'name': name, 'phone': phone, 'address': address}, details='إنشاء مورد')
        return sid

    def update_customer(self, customer_id: int, name: str, phone: str = '', address: str = ''):
        _party_policy().require(_party_policy().OP_CUSTOMER_EDIT, context='update_customer', payload={'id': customer_id, 'name': name})
        old = self.customer_gateway.get(customer_id)
        result = self.customer_gateway.update(customer_id, {'name': name, 'phone': phone, 'address': address})
        new = self.customer_by_id(customer_id)
        audit_service.log('UPDATE', 'CUSTOMER', customer_id, old_values=old, new_values=new, details='تعديل عميل')
        return result

    def update_supplier(self, supplier_id: int, name: str, phone: str = '', address: str = ''):
        _party_policy().require(_party_policy().OP_SUPPLIER_EDIT, context='update_supplier', payload={'id': supplier_id, 'name': name})
        old = self.supplier_gateway.get(supplier_id)
        result = self.supplier_gateway.update(supplier_id, {'name': name, 'phone': phone, 'address': address})
        new = self.supplier_by_id(supplier_id)
        audit_service.log('UPDATE', 'SUPPLIER', supplier_id, old_values=old, new_values=new, details='تعديل مورد')
        return result

    def delete_customer(self, customer_id: int):
        _party_policy().require(_party_policy().OP_CUSTOMER_DELETE, context='delete_customer', payload={'id': customer_id})
        old = self.customer_gateway.get(customer_id)
        result = self.customer_gateway.delete(customer_id)
        audit_service.log('DELETE', 'CUSTOMER', customer_id, old_values=old, details='حذف عميل')
        return result

    def delete_supplier(self, supplier_id: int):
        _party_policy().require(_party_policy().OP_SUPPLIER_DELETE, context='delete_supplier', payload={'id': supplier_id})
        old = self.supplier_gateway.get(supplier_id)
        result = self.supplier_gateway.delete(supplier_id)
        audit_service.log('DELETE', 'SUPPLIER', supplier_id, old_values=old, details='حذف مورد')
        return result


entity_service = EntityService()
