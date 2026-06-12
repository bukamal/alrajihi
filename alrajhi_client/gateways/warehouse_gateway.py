# -*- coding: utf-8 -*-
"""Warehouse gateway contract and factory.

Application services use this contract instead of importing warehouse DAO or
RestClient directly.  Local persistence stays behind the local adapter; remote
mode stays behind the remote adapter.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class WarehouseGateway(ABC):
    @abstractmethod
    def bootstrap(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def list(self, include_archived: bool = False) -> List[Dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def get(self, warehouse_id: int) -> Optional[Dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def create(self, data: Dict[str, Any]) -> int:
        raise NotImplementedError

    @abstractmethod
    def update(self, warehouse_id: int, data: Dict[str, Any]):
        raise NotImplementedError

    @abstractmethod
    def archive(self, warehouse_id: int):
        raise NotImplementedError

    @abstractmethod
    def balances(self, search: str | None = None, warehouse_id: int | None = None,
                 limit: int | None = None, offset: int | None = None) -> List[Dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def balance_count(self, search: str | None = None, warehouse_id: int | None = None) -> int:
        raise NotImplementedError

    @abstractmethod
    def movements(self, item_id: int | None = None, warehouse_id: int | None = None,
                  limit: int = 100) -> List[Dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def default_warehouse_id(self) -> int | None:
        raise NotImplementedError

    @abstractmethod
    def default_warehouse(self) -> Optional[Dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def available_qty(self, item_id: int, warehouse_id: int | None = None):
        raise NotImplementedError

    @abstractmethod
    def record_movement(self, item_id, warehouse_id, movement_type, quantity,
                        unit_cost='0', reference_type=None, reference_id=None, notes=''):
        raise NotImplementedError

    @abstractmethod
    def reverse_reference(self, reference_type, reference_id) -> None:
        raise NotImplementedError

    @abstractmethod
    def transfers(self, limit: int = 200) -> List[Dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def create_transfer(self, data: Dict[str, Any]) -> int:
        raise NotImplementedError

    @abstractmethod
    def cancel_transfer(self, transfer_id: int):
        raise NotImplementedError

    @abstractmethod
    def is_remote(self) -> bool:
        raise NotImplementedError


def create_warehouse_gateway() -> WarehouseGateway:
    """Return the active warehouse gateway.

    Centralizing selection keeps UI/service code independent from whether the
    application currently uses the remote API or the local offline store.
    """
    from database.connection import DatabaseConnection

    db = DatabaseConnection()
    if db.is_remote():
        from gateways.remote.warehouse_gateway import RemoteWarehouseGateway
        return RemoteWarehouseGateway(db.get_rest_client())

    from gateways.local.warehouse_gateway import LocalWarehouseGateway
    return LocalWarehouseGateway()
