# -*- coding: utf-8 -*-
"""Inventory movement gateway contract and factory.

This boundary keeps legacy inventory_movements access out of application
services.  The local adapter may still use InventoryMovementDAO; remote mode
uses explicit REST endpoints instead of DatabaseConnection.execute().
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class InventoryGateway(ABC):
    @abstractmethod
    def movements(self, item_id: int) -> List[Dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def record_movement(self, item_id: int, movement_type: str, quantity,
                        unit_cost, reference_id=None) -> int | None:
        raise NotImplementedError

    @abstractmethod
    def ledger_entries(self, **filters) -> List[Dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def record_ledger_entry(self, data: Dict[str, Any]) -> int | None:
        raise NotImplementedError

    @abstractmethod
    def ledger_balance(self, item_id: int, warehouse_id=None):
        raise NotImplementedError

    @abstractmethod
    def ledger_reconciliation(self, item_id=None, warehouse_id=None, tolerance='0') -> Dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def ledger_dual_read(self, item_id=None, warehouse_id=None, tolerance='0', include_matches=True) -> Dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def ledger_snapshot(self, item_id=None, warehouse_id=None) -> Dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def ledger_health(self, item_id=None, warehouse_id=None, tolerance='0') -> Dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def ledger_backfill(self, dry_run=True, item_id=None, warehouse_id=None, clear_existing=False, include_item_movements=True, include_warehouse_movements=True) -> Dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def ledger_readiness(self, item_id=None, warehouse_id=None, tolerance='0') -> Dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def ledger_controlled_read(self, item_id=None, warehouse_id=None, mode='operational', tolerance='0') -> Dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def is_remote(self) -> bool:
        raise NotImplementedError


def create_inventory_gateway() -> InventoryGateway:
    """Return the active inventory gateway for local or remote mode."""
    from database.connection import DatabaseConnection

    db = DatabaseConnection()
    if db.is_remote():
        from gateways.remote.inventory_gateway import RemoteInventoryGateway
        return RemoteInventoryGateway(db.get_rest_client())

    from gateways.local.inventory_gateway import LocalInventoryGateway
    return LocalInventoryGateway()
