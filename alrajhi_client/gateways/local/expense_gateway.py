# -*- coding: utf-8 -*-
"""Local expense gateway adapter.

This is the only gateway layer allowed to use the legacy expense DAO.
"""
from __future__ import annotations

from typing import Any, Dict, List, Tuple

from core.compat import pair
from database import expense_dao
from gateways.expense_gateway import ExpenseGateway


class LocalExpenseGateway(ExpenseGateway):
    def list(self, search: str | None = None, limit: int | None = None,
             offset: int | None = None) -> Tuple[List[Dict[str, Any]], int]:
        rows, total = pair(expense_dao.get_all(search=search), 'expenses')
        if offset is not None:
            rows = rows[offset:]
        if limit is not None:
            rows = rows[:limit]
        return rows, total

    def create(self, amount, date: str, description: str) -> int:
        return expense_dao.add(amount, date, description)

    def delete(self, expense_id: int):
        return expense_dao.delete(expense_id)

    def is_remote(self) -> bool:
        return False
