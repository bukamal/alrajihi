from __future__ import annotations

import datetime
from typing import Any

from alrajhi_server.database.connection import get_db


class SettingsRepository:
    def get_setting(self, key: str) -> Any | None:
        row = get_db().execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return row["value"] if row else None

    def set_setting(self, key: str, value: Any) -> None:
        db = get_db()
        category = key.split('/')[0] if '/' in str(key) else None
        now = datetime.datetime.now().isoformat(timespec='seconds')
        try:
            db.execute(
                "INSERT OR REPLACE INTO settings (key, value, category, updated_at) VALUES (?, ?, ?, ?)",
                (key, value, category, now),
            )
        except Exception:
            db.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
        db.commit()

    def list_exchange_rates(self) -> list[dict[str, Any]]:
        rows = get_db().execute(
            "SELECT currency_code, rate_to_usd, updated_at FROM exchange_rates ORDER BY currency_code"
        ).fetchall()
        return [dict(row) for row in rows]

    def update_exchange_rate(self, currency_code: str, rate_to_usd: Any) -> None:
        now = datetime.datetime.now().isoformat()
        db = get_db()
        db.execute(
            "INSERT OR REPLACE INTO exchange_rates (currency_code, rate_to_usd, updated_at) VALUES (?, ?, ?)",
            (currency_code, rate_to_usd, now),
        )
        db.commit()

    def historical_rate(self, currency_code: str, effective_date: str) -> Any:
        row = get_db().execute(
            """
            SELECT rate_to_usd FROM exchange_rate_history
            WHERE currency_code = ? AND effective_date <= ?
            ORDER BY effective_date DESC LIMIT 1
            """,
            (currency_code, effective_date),
        ).fetchone()
        return row["rate_to_usd"] if row else 1.0
