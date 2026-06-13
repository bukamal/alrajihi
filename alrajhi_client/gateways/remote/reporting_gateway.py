# -*- coding: utf-8 -*-
"""Remote API reporting gateway adapter."""
from __future__ import annotations

from typing import Any, Dict, List

from gateways.reporting_gateway import ReportingGateway


class RemoteReportingGateway(ReportingGateway):
    def __init__(self, rest_client):
        self.rest_client = rest_client

    def summary(self, start_date: str | None = None, end_date: str | None = None) -> Dict[str, Any]:
        result = self.rest_client.get_summary(start_date=start_date, end_date=end_date)
        return result if isinstance(result, dict) else {}

    def income_statement(self, start_date: str | None = None, end_date: str | None = None) -> Dict[str, Any]:
        result = self.rest_client.get_income_statement(start_date=start_date, end_date=end_date)
        return result if isinstance(result, dict) else {}

    def balance_sheet(self, start_date: str | None = None, end_date: str | None = None) -> Dict[str, Any]:
        result = self.rest_client.get_balance_sheet(start_date=start_date, end_date=end_date)
        return result if isinstance(result, dict) else {}

    def customer_statement(self, customer_id: int, start_date: str | None = None, end_date: str | None = None) -> List[Dict[str, Any]]:
        result = self.rest_client.get_customer_statement(customer_id, start_date=start_date, end_date=end_date)
        return result if isinstance(result, list) else []

    def supplier_statement(self, supplier_id: int, start_date: str | None = None, end_date: str | None = None) -> List[Dict[str, Any]]:
        result = self.rest_client.get_supplier_statement(supplier_id, start_date=start_date, end_date=end_date)
        return result if isinstance(result, list) else []

    def customer_balances(self) -> List[Dict[str, Any]]:
        result = self.rest_client.get_customer_balances()
        return result if isinstance(result, list) else []

    def supplier_balances(self) -> List[Dict[str, Any]]:
        result = self.rest_client.get_supplier_balances()
        return result if isinstance(result, list) else []

    def customer_aging(self, as_of_date: str | None = None) -> List[Dict[str, Any]]:
        result = self.rest_client.get_customer_aging(as_of_date=as_of_date)
        return result if isinstance(result, list) else []

    def supplier_aging(self, as_of_date: str | None = None) -> List[Dict[str, Any]]:
        result = self.rest_client.get_supplier_aging(as_of_date=as_of_date)
        return result if isinstance(result, list) else []

    def trial_balance(self) -> List[Dict[str, Any]]:
        result = self.rest_client.get_trial_balance()
        return result if isinstance(result, list) else []

    def is_remote(self) -> bool:
        return True
