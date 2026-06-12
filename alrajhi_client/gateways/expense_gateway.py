# -*- coding: utf-8 -*-
"""Expense gateway contract and factory.

Phase 7 moves legacy expense-shaped voucher access behind a single
application-facing contract.  UI and service code should not import the
expense DAO directly; local DAO and remote REST details are isolated in
adapters.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Tuple


class ExpenseGateway(ABC):
    @abstractmethod
    def list(self, search: str | None = None, limit: int | None = None,
             offset: int | None = None) -> Tuple[List[Dict[str, Any]], int]:
        raise NotImplementedError

    @abstractmethod
    def create(self, amount, date: str, description: str) -> int:
        raise NotImplementedError

    @abstractmethod
    def delete(self, expense_id: int):
        raise NotImplementedError

    @abstractmethod
    def is_remote(self) -> bool:
        raise NotImplementedError


def create_expense_gateway() -> ExpenseGateway:
    """Return the active expense gateway."""
    from database.connection import DatabaseConnection

    db = DatabaseConnection()
    if db.is_remote():
        from gateways.remote.expense_gateway import RemoteExpenseGateway
        return RemoteExpenseGateway(db.get_rest_client())

    from gateways.local.expense_gateway import LocalExpenseGateway
    return LocalExpenseGateway()
