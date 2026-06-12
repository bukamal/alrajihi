# -*- coding: utf-8 -*-
"""Expense/income dashboard service.

The legacy expense DAO maps expense/receipt vouchers into an old expense-shaped
record.  This service keeps that compatibility but removes direct DAO imports
from UI widgets.
"""
from __future__ import annotations

from typing import Dict, List

from core.compat import records
from gateways.expense_gateway import create_expense_gateway
from core.services.audit_service import audit_service


class ExpenseService:
    """Read/write facade for legacy expense-shaped voucher records."""

    def __init__(self, gateway=None):
        self.gateway = gateway or create_expense_gateway()

    def all(self, search: str | None = None) -> List[Dict]:
        return records(self.gateway.list(search=search), 'expenses')

    def recent(self, limit: int = 5) -> List[Dict]:
        expenses = self.all()
        return sorted(expenses, key=lambda x: x.get('id', 0), reverse=True)[:limit]

    def add(self, amount, date: str, description: str):
        expense_id = self.gateway.create(amount, date, description)
        audit_service.log('CREATE', 'EXPENSE', expense_id, new_values={'amount': str(amount), 'date': date, 'description': description}, details='إنشاء مصروف')
        return expense_id

    def delete(self, expense_id: int):
        old = None
        for rec in self.all():
            if rec.get('id') == expense_id:
                old = rec
                break
        result = self.gateway.delete(expense_id)
        audit_service.log('DELETE', 'EXPENSE', expense_id, old_values=old, details='حذف مصروف')
        return result


expense_service = ExpenseService()
