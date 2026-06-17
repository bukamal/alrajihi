# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any

from alrajhi_server.database.connection import get_db


class AuditEventRepository:
    """Low-level audit event writer used by API helper code."""

    def audit_log_columns(self) -> set[str]:
        try:
            db = get_db()
            return {row[1] for row in db.execute('PRAGMA table_info(audit_log)').fetchall()}
        except Exception:
            return set()

    def get_username(self, user_id: Any) -> str | None:
        try:
            row = get_db().execute('SELECT username FROM users WHERE id=?', (user_id,)).fetchone()
            return row['username'] if row else None
        except Exception:
            return None

    def insert_audit_log(self, data: dict[str, Any]) -> None:
        try:
            db = get_db()
            cols = self.audit_log_columns()
            insert_cols = [c for c in data if c in cols]
            if insert_cols:
                placeholders = ', '.join(['?'] * len(insert_cols))
                db.execute(
                    f"INSERT INTO audit_log ({', '.join(insert_cols)}) VALUES ({placeholders})",
                    tuple(data[c] for c in insert_cols),
                )
                db.commit()
        except Exception:
            pass
