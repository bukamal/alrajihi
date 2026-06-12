# -*- coding: utf-8 -*-
"""Local customer/supplier gateway adapters.

This is the only layer allowed to use the legacy DAO for these entities.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from gateways.entity_gateway import CustomerGateway, SupplierGateway
from database.dao.customer_dao import customer_dao
from database.dao.supplier_dao import supplier_dao


class LocalCustomerGateway(CustomerGateway):
    def list(self, search: str | None = None, limit: int | None = None,
             offset: int | None = None) -> Tuple[List[Dict], int]:
        return customer_dao.get_all(search=search, limit=limit, offset=offset)

    def get(self, customer_id: int) -> Optional[Dict]:
        customer = customer_dao.get_by_id(customer_id)
        return customer if isinstance(customer, dict) else None

    def create(self, data: Dict) -> int:
        return customer_dao.add(data.get('name', ''), data.get('phone', ''), data.get('address', ''))

    def update(self, customer_id: int, data: Dict):
        return customer_dao.update(customer_id, data.get('name', ''), data.get('phone', ''), data.get('address', ''))

    def delete(self, customer_id: int):
        return customer_dao.delete(customer_id)


class LocalSupplierGateway(SupplierGateway):
    def list(self, search: str | None = None, limit: int | None = None,
             offset: int | None = None) -> Tuple[List[Dict], int]:
        return supplier_dao.get_all(search=search, limit=limit, offset=offset)

    def get(self, supplier_id: int) -> Optional[Dict]:
        supplier = supplier_dao.get_by_id(supplier_id)
        return supplier if isinstance(supplier, dict) else None

    def create(self, data: Dict) -> int:
        return supplier_dao.add(data.get('name', ''), data.get('phone', ''), data.get('address', ''))

    def update(self, supplier_id: int, data: Dict):
        return supplier_dao.update(supplier_id, data.get('name', ''), data.get('phone', ''), data.get('address', ''))

    def delete(self, supplier_id: int):
        return supplier_dao.delete(supplier_id)
