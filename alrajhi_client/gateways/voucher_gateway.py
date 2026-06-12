# -*- coding: utf-8 -*-
"""Voucher gateway contract and factory.

Phase 6 wraps voucher persistence behind a single application-facing
contract.  The voucher service no longer imports voucher DAO directly; local
DAO and remote REST details live only in adapters.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple


class VoucherGateway(ABC):
    @abstractmethod
    def list(self, search: str | None = None, vtype: str | None = None,
             limit: int | None = None, offset: int | None = None) -> Tuple[List[Dict[str, Any]], int]:
        raise NotImplementedError

    @abstractmethod
    def get(self, voucher_id: int) -> Optional[Dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def create(self, data: Dict[str, Any]) -> int:
        raise NotImplementedError

    @abstractmethod
    def update(self, voucher_id: int, data: Dict[str, Any]):
        raise NotImplementedError

    @abstractmethod
    def delete(self, voucher_id: int):
        raise NotImplementedError

    @abstractmethod
    def is_remote(self) -> bool:
        raise NotImplementedError


def create_voucher_gateway() -> VoucherGateway:
    """Return the active voucher gateway.

    Selection is centralized here so services and UI code do not depend on
    voucher DAO/repository/database modules directly.
    """
    from database.connection import DatabaseConnection

    db = DatabaseConnection()
    if db.is_remote():
        from gateways.remote.voucher_gateway import RemoteVoucherGateway
        return RemoteVoucherGateway(db.get_rest_client())

    from gateways.local.voucher_gateway import LocalVoucherGateway
    return LocalVoucherGateway()
