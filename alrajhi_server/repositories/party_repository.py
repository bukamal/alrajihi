from __future__ import annotations

from typing import Any

from alrajhi_server.database.connection import get_db


class PartyRepository:
    """CRUD repository for customer/supplier master data."""

    def __init__(self, table_name: str):
        if table_name not in {"customers", "suppliers"}:
            raise ValueError("unsupported party table")
        self.table_name = table_name

    def list(self, user_id: Any, search: str | None = None, limit: int | None = None, offset: int | None = None) -> dict[str, Any]:
        db = get_db()
        query = f"SELECT * FROM {self.table_name} WHERE user_id = ?"
        params: list[Any] = [user_id]
        if search:
            query += " AND (name LIKE ? OR phone LIKE ?)"
            params.extend([f"%{search}%", f"%{search}%"])
        query += " ORDER BY name"
        if limit:
            query += " LIMIT ?"
            params.append(limit)
        if offset:
            query += " OFFSET ?"
            params.append(offset)

        count_query = f"SELECT COUNT(*) FROM {self.table_name} WHERE user_id = ?"
        count_params: list[Any] = [user_id]
        if search:
            count_query += " AND (name LIKE ? OR phone LIKE ?)"
            count_params.extend([f"%{search}%", f"%{search}%"])

        total = db.execute(count_query, count_params).fetchone()[0]
        rows = db.execute(query, params).fetchall()
        return {"rows": [dict(row) for row in rows], "total": total}

    def create(self, user_id: Any, data: dict[str, Any]) -> int:
        db = get_db()
        cursor = db.execute(
            f"""
            INSERT INTO {self.table_name} (user_id, name, phone, address, balance)
            VALUES (?,?,?,?,?)
            """,
            (user_id, data["name"], data.get("phone", ""), data.get("address", ""), data.get("balance", "0")),
        )
        db.commit()
        return int(cursor.lastrowid)

    def update(self, party_id: int, user_id: Any, data: dict[str, Any]) -> None:
        db = get_db()
        db.execute(
            f"""
            UPDATE {self.table_name} SET name=?, phone=?, address=?, balance=?
            WHERE id=? AND user_id=?
            """,
            (data["name"], data.get("phone", ""), data.get("address", ""), data.get("balance", "0"), party_id, user_id),
        )
        db.commit()

    def delete(self, party_id: int, user_id: Any) -> None:
        db = get_db()
        db.execute(f"DELETE FROM {self.table_name} WHERE id=? AND user_id=?", (party_id, user_id))
        db.commit()
