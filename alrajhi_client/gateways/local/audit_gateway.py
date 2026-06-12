# -*- coding: utf-8 -*-
"""Local audit gateway adapter."""
from __future__ import annotations

import datetime
import json
from typing import Any, Optional, Dict, List, Tuple

from auth.session import UserSession
from database.connection import get_session_id
from gateways.audit_gateway import AuditGateway


class LocalAuditGateway(AuditGateway):
    def __init__(self, db):
        self.db = db

    def is_remote(self) -> bool:
        return False

    def _json(self, value: Any) -> str:
        try:
            return json.dumps(value, ensure_ascii=False, default=str, sort_keys=True)
        except Exception:
            return str(value)

    def _columns(self, conn, table: str) -> set[str]:
        try:
            return {row[1] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}
        except Exception:
            return set()

    def ensure_schema(self, conn) -> None:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                username TEXT,
                action TEXT,
                table_name TEXT,
                record_id INTEGER,
                details TEXT,
                ip_address TEXT,
                timestamp TEXT
            )
        """)
        cols = self._columns(conn, 'audit_log')
        for col_name, col_type in [
            ('event_time', 'TEXT'), ('entity_type', 'TEXT'), ('entity_id', 'INTEGER'),
            ('old_values', 'TEXT'), ('new_values', 'TEXT'), ('session_id', 'TEXT'), ('source', 'TEXT')
        ]:
            if col_name not in cols:
                conn.execute(f"ALTER TABLE audit_log ADD COLUMN {col_name} {col_type}")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_log_user ON audit_log(user_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_log_timestamp ON audit_log(timestamp)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_log_entity ON audit_log(entity_type, entity_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_log_action ON audit_log(action)")

    def log(self, action: str, entity_type: str, entity_id: Optional[int] = None,
            old_values: Any = None, new_values: Any = None, details: str = '',
            source: str = 'USER', ip_address: str = '127.0.0.1') -> None:
        conn = self.db.get_connection()
        self.ensure_schema(conn)
        cols = self._columns(conn, 'audit_log')
        now = datetime.datetime.now().isoformat(timespec='seconds')
        user = UserSession.get_current() or {}
        user_id = user.get('id') or UserSession.get_current_user_id()
        username = user.get('username') or user.get('full_name') or 'system'
        detail_payload = details
        if old_values is not None or new_values is not None:
            detail_payload = self._json({'details': details, 'old': old_values, 'new': new_values})

        base = {
            'user_id': user_id,
            'username': username,
            'action': action,
            'table_name': entity_type,
            'record_id': entity_id,
            'details': detail_payload,
            'ip_address': ip_address,
            'timestamp': now,
            'event_time': now,
            'entity_type': entity_type,
            'entity_id': entity_id,
            'old_values': self._json(old_values) if old_values is not None else None,
            'new_values': self._json(new_values) if new_values is not None else None,
            'session_id': get_session_id(),
            'source': source,
        }
        insert_cols = [c for c in base.keys() if c in cols]
        if not insert_cols:
            return
        sql = f"INSERT INTO audit_log ({', '.join(insert_cols)}) VALUES ({', '.join(['?']*len(insert_cols))})"
        conn.execute(sql, tuple(base[c] for c in insert_cols))
        conn.commit()


    def list_logs(self, limit: int = 1000, offset: int = 0, user_id: int | None = None,
                  action: str | None = None, table_name: str | None = None,
                  start_date: str | None = None, end_date: str | None = None) -> Tuple[List[Dict], int]:
        conn = self.db.get_connection()
        self.ensure_schema(conn)
        count_sql = "SELECT COUNT(*) FROM audit_log WHERE 1=1"
        sql = ("SELECT id, user_id, username, action, table_name, record_id, details, "
               "ip_address, timestamp, event_time, entity_type, entity_id, old_values, "
               "new_values, session_id, source FROM audit_log WHERE 1=1")
        params = []
        if user_id:
            count_sql += " AND user_id = ?"
            sql += " AND user_id = ?"
            params.append(user_id)
        if action and action != "الكل":
            count_sql += " AND action = ?"
            sql += " AND action = ?"
            params.append(action)
        if table_name and table_name != "الكل":
            count_sql += " AND table_name = ?"
            sql += " AND table_name = ?"
            params.append(table_name)
        if start_date:
            count_sql += " AND timestamp >= ?"
            sql += " AND timestamp >= ?"
            params.append(start_date)
        if end_date:
            count_sql += " AND timestamp <= ?"
            sql += " AND timestamp <= ?"
            params.append(end_date + " 23:59:59")
        cur = conn.execute(count_sql, tuple(params))
        total = cur.fetchone()[0]
        sql += " ORDER BY id DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        rows = conn.execute(sql, tuple(params)).fetchall()
        result = [dict(row) if not isinstance(row, dict) else row for row in rows]
        return result, total

    def delete_old_logs(self, days: int = 90) -> None:
        conn = self.db.get_connection()
        self.ensure_schema(conn)
        cutoff = (datetime.datetime.now() - datetime.timedelta(days=days)).isoformat()
        conn.execute("DELETE FROM audit_log WHERE timestamp < ?", (cutoff,))
        conn.commit()
