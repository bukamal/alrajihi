# -*- coding: utf-8 -*-
from __future__ import annotations

import datetime
from typing import Any

from alrajhi_server.database.connection import get_db


class AuthRepository:
    """Authentication persistence for server API routes."""

    def get_user_by_username(self, username: str | None):
        return get_db().execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()

    def get_username(self, user_id: Any) -> str | None:
        row = get_db().execute('SELECT username FROM users WHERE id = ?', (user_id,)).fetchone()
        return row['username'] if row else None

    def mark_last_login(self, user_id: Any, timestamp: str | None = None) -> None:
        db = get_db()
        db.execute("UPDATE users SET last_login = ? WHERE id = ?", (timestamp or datetime.datetime.now().isoformat(), user_id))
        db.commit()

    def add_token_to_blacklist(self, jti: str, timestamp: str | None = None) -> None:
        db = get_db()
        db.execute('INSERT INTO token_blacklist (jti, created_at) VALUES (?, ?)', (jti, timestamp or datetime.datetime.now().isoformat()))
        db.commit()

    def record_auth_event(self, *, user_id: Any, username: str, action: str, table_name: str, record_id: Any, ip_address: str | None, timestamp: str | None = None) -> None:
        db = get_db()
        now = timestamp or datetime.datetime.now().isoformat()
        db.execute('''
            INSERT INTO audit_log (user_id, username, action, table_name, record_id, details, ip_address, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, username, action, table_name, record_id, '', ip_address or '', now))
        db.commit()
