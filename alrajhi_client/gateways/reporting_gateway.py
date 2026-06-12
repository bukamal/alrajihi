# -*- coding: utf-8 -*-
"""Reporting gateway contract and factory.

Phase 8 moves financial/reporting reads behind a single application-facing
contract.  ReportingService no longer imports ReportingDAO directly; local DAO
and remote REST report endpoints are isolated in adapters.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class ReportingGateway(ABC):
    @abstractmethod
    def summary(self, start_date: str | None = None, end_date: str | None = None) -> Dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def income_statement(self, start_date: str | None = None, end_date: str | None = None) -> Dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def balance_sheet(self, start_date: str | None = None, end_date: str | None = None) -> Dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def customer_statement(self, customer_id: int) -> List[Dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def supplier_statement(self, supplier_id: int) -> List[Dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def trial_balance(self) -> List[Dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def is_remote(self) -> bool:
        raise NotImplementedError


def create_reporting_gateway() -> ReportingGateway:
    """Return the active reporting gateway."""
    from database.connection import DatabaseConnection

    db = DatabaseConnection()
    if db.is_remote():
        from gateways.remote.reporting_gateway import RemoteReportingGateway
        return RemoteReportingGateway(db.get_rest_client())

    from gateways.local.reporting_gateway import LocalReportingGateway
    return LocalReportingGateway()
