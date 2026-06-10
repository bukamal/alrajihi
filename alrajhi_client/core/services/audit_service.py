# -*- coding: utf-8 -*-
"""Audit log application service.

This service records traceable business events with backwards-compatible audit_log
columns and optional structured before/after payloads when the database has been
migrated.  Calls are best-effort: audit failure must never break the business
operation that already succeeded.
"""
from __future__ import annotations

import json
import socket
import datetime
from typing import Any, Dict, Optional

from auth.session import UserSession
from database.connection import DatabaseConnection, get_session_id


class AuditService:
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

    def log(self, action: str, entity_type: str, entity_id: Optional[int] = None,
            old_values: Any = None, new_values: Any = None, details: str = '',
            source: str = 'USER', ip_address: str = '127.0.0.1') -> None:
        try:
            db = DatabaseConnection()
            if db.is_remote():
                # In client/server mode the server is authoritative for audit entries.
                return
            conn = db.get_connection()
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
        except Exception:
            # Audit must not interrupt business workflows.
            pass


audit_service = AuditService()
