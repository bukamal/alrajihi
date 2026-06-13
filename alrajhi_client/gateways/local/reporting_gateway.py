# -*- coding: utf-8 -*-
"""Local reporting gateway adapter."""
from __future__ import annotations

from typing import Any, Dict, List

from database.dao.reporting_dao import ReportingDAO
from gateways.reporting_gateway import ReportingGateway


class LocalReportingGateway(ReportingGateway):
    def __init__(self):
        self._dao = ReportingDAO()

    def summary(self, start_date: str | None = None, end_date: str | None = None) -> Dict[str, Any]:
        result = self._dao.get_summary_filtered(start_date, end_date) if (start_date or end_date) else self._dao.get_summary()
        return result if isinstance(result, dict) else {}

    def income_statement(self, start_date: str | None = None, end_date: str | None = None) -> Dict[str, Any]:
        result = self._dao.get_income_statement_filtered(start_date, end_date)
        return result if isinstance(result, dict) else {}

    def balance_sheet(self, start_date: str | None = None, end_date: str | None = None) -> Dict[str, Any]:
        result = self._dao.get_balance_sheet_filtered(start_date, end_date)
        return result if isinstance(result, dict) else {}

    def customer_statement(self, customer_id: int, start_date: str | None = None, end_date: str | None = None) -> List[Dict[str, Any]]:
        result = self._dao.get_customer_statement(customer_id, start_date, end_date)
        return result if isinstance(result, list) else []

    def supplier_statement(self, supplier_id: int, start_date: str | None = None, end_date: str | None = None) -> List[Dict[str, Any]]:
        result = self._dao.get_supplier_statement(supplier_id, start_date, end_date)
        return result if isinstance(result, list) else []

    def customer_balances(self) -> List[Dict[str, Any]]:
        result = self._dao.get_customer_balances()
        return result if isinstance(result, list) else []

    def supplier_balances(self) -> List[Dict[str, Any]]:
        result = self._dao.get_supplier_balances()
        return result if isinstance(result, list) else []

    def customer_aging(self, as_of_date: str | None = None) -> List[Dict[str, Any]]:
        result = self._dao.get_customer_aging(as_of_date)
        return result if isinstance(result, list) else []

    def supplier_aging(self, as_of_date: str | None = None) -> List[Dict[str, Any]]:
        result = self._dao.get_supplier_aging(as_of_date)
        return result if isinstance(result, list) else []

    def trial_balance(self) -> List[Dict[str, Any]]:
        result = self._dao.get_trial_balance()
        return result if isinstance(result, list) else []

    def is_remote(self) -> bool:
        return False
