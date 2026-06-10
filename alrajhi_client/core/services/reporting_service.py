# -*- coding: utf-8 -*-
"""Reporting service facade for dashboard and reports UI.

This service centralizes report access and keeps widgets independent from the
legacy reporting DAO contract.  The DAO/repository layer remains in place for
backward compatibility; UI code should prefer this service.
"""
from __future__ import annotations

from typing import Dict, List

from database.dao.reporting_dao import ReportingDAO


class ReportingService:
    """Read-only reporting facade over the legacy reporting DAO."""

    def __init__(self):
        self._dao = ReportingDAO()

    def summary(self, start_date: str | None = None, end_date: str | None = None) -> Dict:
        if start_date or end_date:
            result = self._dao.get_summary_filtered(start_date, end_date)
        else:
            result = self._dao.get_summary()
        return result if isinstance(result, dict) else {}

    def income_statement(self, start_date: str | None = None, end_date: str | None = None) -> Dict:
        result = self._dao.get_income_statement_filtered(start_date, end_date)
        return result if isinstance(result, dict) else {}

    def balance_sheet(self, start_date: str | None = None, end_date: str | None = None) -> Dict:
        result = self._dao.get_balance_sheet_filtered(start_date, end_date)
        return result if isinstance(result, dict) else {}

    def customer_statement(self, customer_id: int) -> List[Dict]:
        result = self._dao.get_customer_statement(customer_id)
        return result if isinstance(result, list) else []

    def supplier_statement(self, supplier_id: int) -> List[Dict]:
        result = self._dao.get_supplier_statement(supplier_id)
        return result if isinstance(result, list) else []

    def trial_balance(self) -> List[Dict]:
        result = self._dao.get_trial_balance()
        return result if isinstance(result, list) else []


reporting_service = ReportingService()
