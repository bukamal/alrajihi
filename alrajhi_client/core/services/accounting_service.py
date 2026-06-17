# -*- coding: utf-8 -*-
"""Accounting service facade.

The service layer intentionally delegates persistence/reporting operations to an
accounting gateway so core services do not access DatabaseConnection or SQL
directly.
"""
from __future__ import annotations

from gateways.accounting_gateway import create_accounting_gateway


class AccountingService:
    def __init__(self, gateway=None):
        self._gateway = gateway or create_accounting_gateway()
        self.DEFAULT_ACCOUNTS = getattr(self._gateway, 'DEFAULT_ACCOUNTS', [])

    def __getattr__(self, name):
        return getattr(self._gateway, name)


accounting_service = AccountingService()
