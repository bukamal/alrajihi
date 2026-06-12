# -*- coding: utf-8 -*-
"""Cashbox/bank gateway contract and factory.

The service layer uses this contract instead of importing cashbox DAO or
RestClient directly.  Local DAO access is confined to the local adapter; remote
API access is confined to the remote adapter.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class CashboxGateway(ABC):
    @abstractmethod
    def bootstrap(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def cashboxes(self, include_archived: bool = False) -> List[Dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def bank_accounts(self, include_archived: bool = False) -> List[Dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def get_cashbox(self, cashbox_id: int) -> Optional[Dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def get_bank_account(self, bank_account_id: int) -> Optional[Dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def default_cashbox_id(self, branch_id: int | None = None) -> Optional[int]:
        raise NotImplementedError

    @abstractmethod
    def add_cashbox(self, data: Dict[str, Any]) -> int:
        raise NotImplementedError

    @abstractmethod
    def update_cashbox(self, cashbox_id: int, data: Dict[str, Any]):
        raise NotImplementedError

    @abstractmethod
    def archive_cashbox(self, cashbox_id: int):
        raise NotImplementedError

    @abstractmethod
    def add_bank_account(self, data: Dict[str, Any]) -> int:
        raise NotImplementedError

    @abstractmethod
    def update_bank_account(self, bank_account_id: int, data: Dict[str, Any]):
        raise NotImplementedError

    @abstractmethod
    def archive_bank_account(self, bank_account_id: int):
        raise NotImplementedError

    @abstractmethod
    def movements(self, limit: int = 200, cashbox_id: int | None = None,
                  bank_account_id: int | None = None) -> List[Dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def record_movement(self, data: Dict[str, Any]) -> int | None:
        raise NotImplementedError

    @abstractmethod
    def delete_reference_movements(self, reference_type, reference_id):
        raise NotImplementedError

    @abstractmethod
    def current_open_shift(self, cashbox_id: int | None = None):
        raise NotImplementedError

    @abstractmethod
    def shifts(self, limit: int = 100, status: str | None = None) -> List[Dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def open_shift(self, data: Dict[str, Any]) -> int | None:
        raise NotImplementedError

    @abstractmethod
    def shift_summary(self, shift_id: int):
        raise NotImplementedError

    @abstractmethod
    def close_shift(self, shift_id: int, actual_amount, notes: str = ''):
        raise NotImplementedError


def create_cashbox_gateway() -> CashboxGateway:
    """Return the active cashbox/bank gateway."""
    from database.connection import DatabaseConnection

    db = DatabaseConnection()
    if db.is_remote():
        from gateways.remote.cashbox_gateway import RemoteCashboxGateway
        return RemoteCashboxGateway(db.get_rest_client())

    from gateways.local.cashbox_gateway import LocalCashboxGateway
    return LocalCashboxGateway()
