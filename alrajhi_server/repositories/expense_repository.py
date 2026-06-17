from __future__ import annotations

import datetime
from typing import Any

from alrajhi_server.database.connection import get_db


class ExpenseRepository:
    def list(self, user_id: Any, limit: int | None = None, offset: int | None = None) -> dict[str, Any]:
        db = get_db()
        total = db.execute("SELECT COUNT(*) FROM vouchers WHERE user_id=? AND type='expense'", (user_id,)).fetchone()[0]
        query = "SELECT * FROM vouchers WHERE user_id=? AND type='expense' ORDER BY id DESC"
        params: list[Any] = [user_id]
        if limit is not None:
            query += " LIMIT ?"
            params.append(limit)
        if offset is not None:
            query += " OFFSET ?"
            params.append(offset)
        rows = db.execute(query, params).fetchall()
        return {"expenses": [dict(row) for row in rows], "total": total}

    def create(self, user_id: Any, data: dict[str, Any]) -> int:
        db = get_db()
        now = datetime.datetime.now().isoformat()
        cursor = db.execute(
            """
            INSERT INTO vouchers (user_id, type, date, amount, description, reference, customer_id, supplier_id, invoice_id, exchange_rate_to_usd, original_currency)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                user_id,
                "expense",
                data.get("date", now[:10]),
                str(data.get("amount", 0)),
                data.get("description", ""),
                data.get("reference", ""),
                None,
                data.get("supplier_id"),
                None,
                data.get("exchange_rate_to_usd", 1.0),
                data.get("original_currency", "USD"),
            ),
        )
        db.commit()
        return int(cursor.lastrowid)

    def update(self, expense_id: int, user_id: Any, data: dict[str, Any]) -> None:
        db = get_db()
        db.execute(
            """
            UPDATE vouchers SET date=?, amount=?, description=?, reference=?, supplier_id=?, exchange_rate_to_usd=?, original_currency=?
            WHERE id=? AND user_id=? AND type='expense'
            """,
            (
                data.get("date"),
                str(data.get("amount", 0)),
                data.get("description", ""),
                data.get("reference", ""),
                data.get("supplier_id"),
                data.get("exchange_rate_to_usd", 1.0),
                data.get("original_currency", "USD"),
                expense_id,
                user_id,
            ),
        )
        db.commit()

    def delete(self, expense_id: int, user_id: Any) -> None:
        db = get_db()
        db.execute("DELETE FROM vouchers WHERE id=? AND user_id=? AND type='expense'", (expense_id, user_id))
        db.commit()
