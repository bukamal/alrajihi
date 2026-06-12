# -*- coding: utf-8 -*-
"""Purchase return gateway contract and factory.

Phase 12 keeps existing purchase-return business behavior intact while moving
remote/local data access behind a single gateway boundary.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple


class PurchaseReturnException(Exception):
    pass


class PurchaseReturnGateway(ABC):
    @abstractmethod
    def next_return_no(self) -> str: raise NotImplementedError

    @abstractmethod
    def list_returns(self, search: str | None = None, limit: int | None = None, offset: int | None = None) -> Tuple[List[Dict[str, Any]], int]: raise NotImplementedError

    @abstractmethod
    def get(self, return_id: int) -> Optional[Dict[str, Any]]: raise NotImplementedError

    @abstractmethod
    def purchase_invoices(self, search: str | None = None, limit: int = 200) -> List[Dict[str, Any]]: raise NotImplementedError

    @abstractmethod
    def returned_qty(self, invoice_id: int, line_id: int | None = None, item_id: int | None = None) -> Decimal: raise NotImplementedError

    @abstractmethod
    def invoice_returnable_lines(self, invoice_id: int) -> List[Dict[str, Any]]: raise NotImplementedError

    @abstractmethod
    def create_return(self, data: Dict[str, Any]) -> int: raise NotImplementedError

    @abstractmethod
    def delete_return(self, return_id: int) -> None: raise NotImplementedError

    @abstractmethod
    def is_remote(self) -> bool: raise NotImplementedError


def create_purchase_return_gateway() -> PurchaseReturnGateway:
    from database.connection import DatabaseConnection

    db = DatabaseConnection()
    if db.is_remote():
        from gateways.remote.purchase_return_gateway import RemotePurchaseReturnGateway
        return RemotePurchaseReturnGateway(db.get_rest_client())

    from gateways.local.purchase_return_gateway import LocalPurchaseReturnGateway
    return LocalPurchaseReturnGateway()
