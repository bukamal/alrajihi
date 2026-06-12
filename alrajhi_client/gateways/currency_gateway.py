# -*- coding: utf-8 -*-
"""Currency gateway contract and factory.

Phase 18 moves exchange-rate persistence behind the Gateway boundary so
CurrencyManager no longer talks to DatabaseConnection/SQL directly.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, List, Optional


class CurrencyGateway(ABC):
    @abstractmethod
    def get_all_currencies(self) -> List[Dict]:
        raise NotImplementedError

    @abstractmethod
    def get_current_rate(self, currency_code: str) -> Optional[float]:
        raise NotImplementedError

    @abstractmethod
    def get_historical_rate(self, currency_code: str, date: str) -> Optional[float]:
        raise NotImplementedError

    @abstractmethod
    def update_rate(self, currency_code: str, rate_to_usd: float) -> None:
        raise NotImplementedError


def create_currency_gateway() -> CurrencyGateway:
    from database.connection import DatabaseConnection

    db = DatabaseConnection()
    if db.is_remote():
        from gateways.remote.currency_gateway import RemoteCurrencyGateway
        return RemoteCurrencyGateway(db.get_rest_client())

    from gateways.local.currency_gateway import LocalCurrencyGateway
    return LocalCurrencyGateway()
