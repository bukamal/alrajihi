# -*- coding: utf-8 -*-
from __future__ import annotations

import datetime
from typing import Any

from alrajhi_server.database.connection import get_db


def _now() -> str:
    return datetime.datetime.now().isoformat()


def _rowdict(row):
    return dict(row) if row else None


class BranchRepository:
    """Branch persistence for server API routes."""

    def ensure_default_branch(self, user_id: Any) -> int:
        db = get_db()
        row = db.execute("SELECT id FROM branches WHERE user_id=? AND is_default=1 AND deleted_at IS NULL LIMIT 1", (user_id,)).fetchone()
        if row:
            return int(row['id'])
        row = db.execute("SELECT id FROM branches WHERE user_id=? AND deleted_at IS NULL ORDER BY id LIMIT 1", (user_id,)).fetchone()
        if row:
            return int(row['id'])
        now = _now()
        cur = db.execute("""
            INSERT INTO branches (user_id, name, code, address, phone, notes, is_default, is_active, created_at, updated_at)
            VALUES (?, ?, ?, '', '', ?, 1, 1, ?, ?)
        """, (user_id, 'الفرع الرئيسي', 'MAIN', 'تم إنشاؤه تلقائياً', now, now))
        db.commit()
        return int(cur.lastrowid)

    def list(self, user_id: Any, include_archived: bool = False) -> list[dict[str, Any]]:
        db = get_db()
        self.ensure_default_branch(user_id)
        sql = """
            SELECT b.*, COUNT(DISTINCT w.id) AS warehouse_count
            FROM branches b
            LEFT JOIN warehouses w ON w.branch_id=b.id AND w.user_id=b.user_id AND w.deleted_at IS NULL
            WHERE b.user_id=?
        """
        params: list[Any] = [user_id]
        if not include_archived:
            sql += " AND b.deleted_at IS NULL AND COALESCE(b.is_active,1)=1"
        sql += " GROUP BY b.id ORDER BY b.is_default DESC, b.name"
        return [_rowdict(r) for r in db.execute(sql, params).fetchall()]

    def get(self, branch_id: int, user_id: Any) -> dict[str, Any] | None:
        return _rowdict(get_db().execute('SELECT * FROM branches WHERE id=? AND user_id=?', (branch_id, user_id)).fetchone())

    def create(self, user_id: Any, payload: dict[str, Any]) -> int:
        db = get_db()
        now = _now()
        cur = db.execute("""
            INSERT INTO branches (user_id, name, code, address, phone, notes, is_default, is_active, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, 0, ?, ?, ?)
        """, (user_id, payload['name'], payload['code'], payload['address'], payload['phone'], payload['notes'], payload['is_active'], now, now))
        db.commit()
        return int(cur.lastrowid)

    def update(self, branch_id: int, user_id: Any, payload: dict[str, Any]) -> None:
        db = get_db()
        db.execute(
            'UPDATE branches SET name=?, code=?, address=?, phone=?, notes=?, is_active=?, updated_at=? WHERE id=? AND user_id=?',
            (payload['name'], payload['code'], payload['address'], payload['phone'], payload['notes'], payload['is_active'], _now(), branch_id, user_id),
        )
        db.commit()

    def archive(self, branch_id: int, user_id: Any) -> tuple[bool, str | None]:
        db = get_db()
        row = db.execute('SELECT is_default FROM branches WHERE id=? AND user_id=?', (branch_id, user_id)).fetchone()
        if not row:
            return False, 'not found'
        if int(row['is_default'] or 0) == 1:
            return False, 'لا يمكن أرشفة الفرع الرئيسي'
        now = _now()
        db.execute('UPDATE branches SET deleted_at=?, is_active=0, updated_at=? WHERE id=? AND user_id=?', (now, now, branch_id, user_id))
        db.commit()
        return True, None
