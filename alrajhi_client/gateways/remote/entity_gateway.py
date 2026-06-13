# -*- coding: utf-8 -*-
"""Remote API customer/supplier gateway adapters."""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from gateways.entity_gateway import CustomerGateway, SupplierGateway


class RemoteCustomerGateway(CustomerGateway):
    def __init__(self, rest_client):
        self.rest_client = rest_client

    def list(self, search: str | None = None, limit: int | None = None,
             offset: int | None = None) -> Tuple[List[Dict], int]:
        return self.rest_client.get_customers(search=search, limit=limit, offset=offset)

    def get(self, customer_id: int) -> Optional[Dict]:
        customers, _ = self.list()
        for customer in customers:
            if int(customer.get('id', 0)) == int(customer_id):
                return customer
        return None

    def create(self, data: Dict) -> int:
        return self.rest_client.add_customer(data)

    def update(self, customer_id: int, data: Dict):
        return self.rest_client.update_customer(customer_id, data)

    def delete(self, customer_id: int):
        return self.rest_client.delete_customer(customer_id)


    def is_remote(self) -> bool:
        return True

class RemoteSupplierGateway(SupplierGateway):
    def __init__(self, rest_client):
        self.rest_client = rest_client

    def list(self, search: str | None = None, limit: int | None = None,
             offset: int | None = None) -> Tuple[List[Dict], int]:
        return self.rest_client.get_suppliers(search=search, limit=limit, offset=offset)

    def get(self, supplier_id: int) -> Optional[Dict]:
        suppliers, _ = self.list()
        for supplier in suppliers:
            if int(supplier.get('id', 0)) == int(supplier_id):
                return supplier
        return None

    def create(self, data: Dict) -> int:
        return self.rest_client.add_supplier(data)

    def update(self, supplier_id: int, data: Dict):
        return self.rest_client.update_supplier(supplier_id, data)

    def delete(self, supplier_id: int):
        return self.rest_client.delete_supplier(supplier_id)

    def is_remote(self) -> bool:
        return True
