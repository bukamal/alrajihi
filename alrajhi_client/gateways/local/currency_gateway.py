# -*- coding: utf-8 -*-
"""Local currency gateway adapter."""
from __future__ import annotations

import datetime
from typing import Dict, List, Optional

from database.connection import DatabaseConnection
from gateways.currency_gateway import CurrencyGateway


class LocalCurrencyGateway(CurrencyGateway):
    def __init__(self):
        self.db = DatabaseConnection()

    def get_all_currencies(self) -> List[Dict]:
        conn = self.db.get_connection()
        rows = conn.execute(
            "SELECT currency_code, rate_to_usd, updated_at FROM exchange_rates ORDER BY currency_code"
        ).fetchall()
        return [dict(row) for row in rows]

    def get_current_rate(self, currency_code: str) -> Optional[float]:
        conn = self.db.get_connection()
        row = conn.execute(
            "SELECT rate_to_usd FROM exchange_rates WHERE currency_code=?",
            (currency_code,),
        ).fetchone()
        return float(row["rate_to_usd"]) if row else None

    def get_historical_rate(self, currency_code: str, date: str) -> Optional[float]:
        conn = self.db.get_connection()
        row = conn.execute(
            """
            SELECT rate_to_usd FROM exchange_rate_history
            WHERE currency_code = ? AND effective_date <= ?
            ORDER BY effective_date DESC LIMIT 1
            """,
            (currency_code, date),
        ).fetchone()
        return float(row["rate_to_usd"]) if row else None

    def update_rate(self, currency_code: str, rate_to_usd: float) -> None:
        conn = self.db.get_connection()
        now = datetime.datetime.now().isoformat()
        conn.execute(
            "INSERT OR REPLACE INTO exchange_rates (currency_code, rate_to_usd, updated_at) VALUES (?, ?, ?)",
            (currency_code, rate_to_usd, now),
        )
        conn.commit()

    def is_remote(self) -> bool:
        return False
