# -*- coding: utf-8 -*-
"""Invoice gateway contract and factory.

Phase 5 intentionally wraps the existing invoice persistence behavior without
changing invoice business rules.  The application service depends on this
contract; local DAO and remote REST details are confined to adapters.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple


class InvoiceGateway(ABC):
    @abstractmethod
    def list(self, search: str | None = None, inv_type: str | None = None,
             start_date: str | None = None, end_date: str | None = None,
             customer_id: int | None = None, supplier_id: int | None = None,
             limit: int | None = None, offset: int | None = None) -> Tuple[List[Dict[str, Any]], int]:
        raise NotImplementedError

    @abstractmethod
    def get(self, invoice_id: int) -> Optional[Dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def create(self, data: Dict[str, Any]) -> int:
        raise NotImplementedError

    @abstractmethod
    def update(self, invoice_id: int, data: Dict[str, Any]):
        raise NotImplementedError

    @abstractmethod
    def delete(self, invoice_id: int):
        raise NotImplementedError

    @abstractmethod
    def next_reference(self, inv_type: str) -> str:
        raise NotImplementedError

    @abstractmethod
    def has_linked_vouchers(self, invoice_id: int) -> bool:
        raise NotImplementedError

    @abstractmethod
    def has_linked_returns(self, invoice_id: int) -> bool:
        raise NotImplementedError

    @abstractmethod
    def is_remote(self) -> bool:
        raise NotImplementedError


def create_invoice_gateway() -> InvoiceGateway:
    """Return the active invoice gateway.

    Selection is centralized here so invoice services and UI code never import
    invoice DAO/repository/database modules directly.
    """
    from database.connection import DatabaseConnection

    db = DatabaseConnection()
    if db.is_remote():
        from gateways.remote.invoice_gateway import RemoteInvoiceGateway
        return RemoteInvoiceGateway(db.get_rest_client())

    from gateways.local.invoice_gateway import LocalInvoiceGateway
    return LocalInvoiceGateway()
