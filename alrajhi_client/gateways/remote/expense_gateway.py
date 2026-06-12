# -*- coding: utf-8 -*-
"""Remote API expense gateway adapter."""
from __future__ import annotations

from typing import Any, Dict, List, Tuple

from gateways.expense_gateway import ExpenseGateway


class RemoteExpenseGateway(ExpenseGateway):
    def __init__(self, rest_client):
        self.rest_client = rest_client

    def list(self, search: str | None = None, limit: int | None = None,
             offset: int | None = None) -> Tuple[List[Dict[str, Any]], int]:
        rows, total = self.rest_client.get_expenses(limit=limit, offset=offset)
        if search:
            needle = search.lower()
            rows = [row for row in rows if needle in str(row.get('description', '')).lower()]
            total = len(rows)
        return rows, total

    def create(self, amount, date: str, description: str) -> int:
        return self.rest_client.add_expense({
            'amount': amount,
            'date': date,
            'description': description,
        })

    def delete(self, expense_id: int):
        return self.rest_client.delete_expense(expense_id)

    def is_remote(self) -> bool:
        return True
