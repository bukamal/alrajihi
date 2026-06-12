# -*- coding: utf-8 -*-
"""Remote currency gateway adapter."""
from __future__ import annotations

from typing import Dict, List, Optional

from gateways.currency_gateway import CurrencyGateway


class RemoteCurrencyGateway(CurrencyGateway):
    def __init__(self, client):
        self.client = client

    def get_all_currencies(self) -> List[Dict]:
        if self.client is None or getattr(self.client, "token", None) is None:
            return []
        return self.client.get_all_currencies()

    def get_current_rate(self, currency_code: str) -> Optional[float]:
        for row in self.get_all_currencies():
            if row.get("currency_code") == currency_code:
                return float(row.get("rate_to_usd", 1.0))
        return None

    def get_historical_rate(self, currency_code: str, date: str) -> Optional[float]:
        if self.client is None:
            return None
        return float(self.client.get_historical_rate(currency_code, date))

    def update_rate(self, currency_code: str, rate_to_usd: float) -> None:
        if self.client is not None:
            self.client.update_exchange_rate(currency_code, rate_to_usd)
