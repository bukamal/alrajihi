# -*- coding: utf-8 -*-
"""Customer/supplier gateway contracts and factory."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple


class CustomerGateway(ABC):
    @abstractmethod
    def list(self, search: str | None = None, limit: int | None = None,
             offset: int | None = None) -> Tuple[List[Dict], int]:
        raise NotImplementedError

    @abstractmethod
    def get(self, customer_id: int) -> Optional[Dict]:
        raise NotImplementedError

    @abstractmethod
    def create(self, data: Dict) -> int:
        raise NotImplementedError

    @abstractmethod
    def update(self, customer_id: int, data: Dict):
        raise NotImplementedError

    @abstractmethod
    def delete(self, customer_id: int):
        raise NotImplementedError


class SupplierGateway(ABC):
    @abstractmethod
    def list(self, search: str | None = None, limit: int | None = None,
             offset: int | None = None) -> Tuple[List[Dict], int]:
        raise NotImplementedError

    @abstractmethod
    def get(self, supplier_id: int) -> Optional[Dict]:
        raise NotImplementedError

    @abstractmethod
    def create(self, data: Dict) -> int:
        raise NotImplementedError

    @abstractmethod
    def update(self, supplier_id: int, data: Dict):
        raise NotImplementedError

    @abstractmethod
    def delete(self, supplier_id: int):
        raise NotImplementedError


def create_entity_gateways():
    """Return the active customer/supplier gateways.

    The selection is centralized here so services and UI code do not need to know
    whether the app is using the remote API or the local offline store.
    """
    from database.connection import DatabaseConnection

    db = DatabaseConnection()
    if db.is_remote():
        from gateways.remote.entity_gateway import RemoteCustomerGateway, RemoteSupplierGateway
        rest_client = db.get_rest_client()
        return RemoteCustomerGateway(rest_client), RemoteSupplierGateway(rest_client)

    from gateways.local.entity_gateway import LocalCustomerGateway, LocalSupplierGateway
    return LocalCustomerGateway(), LocalSupplierGateway()
