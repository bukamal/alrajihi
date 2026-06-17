from __future__ import annotations

import datetime
from typing import Any

from alrajhi_server.database.connection import get_db


class UserRepository:
    """User administration persistence for server API routes."""

    def _sync_rbac_user_role(self, db, user_id: Any, role: str | None, branch_id: Any = None) -> None:
        try:
            role_name = str(role or 'viewer').lower()
            row = db.execute('SELECT id FROM roles WHERE name=?', (role_name,)).fetchone()
            if row:
                db.execute('DELETE FROM user_roles WHERE user_id=?', (str(user_id),))
                cols = {r[1] for r in db.execute('PRAGMA table_info(user_roles)').fetchall()}
                if 'branch_id' in cols:
                    db.execute('INSERT OR IGNORE INTO user_roles(user_id, role_id, branch_id) VALUES (?,?,?)', (str(user_id), row['id'], branch_id))
                else:
                    db.execute('INSERT OR IGNORE INTO user_roles(user_id, role_id) VALUES (?,?)', (str(user_id), row['id']))
            if branch_id is not None and db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='user_branch_access'").fetchone():
                db.execute('DELETE FROM user_branch_access WHERE user_id=?', (str(user_id),))
                db.execute('INSERT OR IGNORE INTO user_branch_access(user_id, branch_id) VALUES (?,?)', (str(user_id), branch_id))
        except Exception:
            pass

    def list(self) -> list[dict[str, Any]]:
        db = get_db()
        if db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='branches'").fetchone():
            rows = db.execute("SELECT u.id, u.username, u.full_name, u.role, u.branch_id, b.name AS branch_name, u.created_at, u.last_login FROM users u LEFT JOIN branches b ON b.id=u.branch_id").fetchall()
        else:
            rows = db.execute("SELECT id, username, full_name, role, branch_id, created_at, last_login FROM users").fetchall()
        return [dict(row) for row in rows]

    def create(self, data: dict[str, Any], password_hash: str, salt: str) -> int:
        db = get_db()
        now = datetime.datetime.now().isoformat()
        user_cols = {r[1] for r in db.execute('PRAGMA table_info(users)').fetchall()}
        branch_id = data.get('branch_id')
        role = data.get('role', 'viewer')
        if 'branch_id' in user_cols:
            cursor = db.execute('''
                INSERT INTO users (username, password_hash, salt, full_name, role, branch_id, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (data['username'], password_hash, salt, data.get('full_name', ''), role, branch_id, now))
        else:
            cursor = db.execute('''
                INSERT INTO users (username, password_hash, salt, full_name, role, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (data['username'], password_hash, salt, data.get('full_name', ''), role, now))
        self._sync_rbac_user_role(db, cursor.lastrowid, role, branch_id)
        db.commit()
        return int(cursor.lastrowid)

    def update(self, user_id: int, data: dict[str, Any]) -> None:
        db = get_db()
        user_cols = {r[1] for r in db.execute('PRAGMA table_info(users)').fetchall()}
        branch_id = data.get('branch_id')
        role = data.get('role', 'viewer')
        if 'branch_id' in user_cols:
            db.execute('UPDATE users SET full_name=?, role=?, branch_id=? WHERE id=?', (data.get('full_name', ''), role, branch_id, user_id))
        else:
            db.execute('UPDATE users SET full_name=?, role=? WHERE id=?', (data.get('full_name', ''), role, user_id))
        self._sync_rbac_user_role(db, user_id, role, branch_id)
        db.commit()

    def delete(self, user_id: int) -> None:
        db = get_db()
        db.execute('DELETE FROM users WHERE id=?', (user_id,))
        db.commit()

    def get_password_record(self, user_id: Any):
        return get_db().execute('SELECT password_hash, salt FROM users WHERE id=?', (user_id,)).fetchone()

    def update_password(self, user_id: Any, password_hash: str, salt: str) -> None:
        db = get_db()
        db.execute('UPDATE users SET password_hash=?, salt=?, force_password_change=0 WHERE id=?', (password_hash, salt, user_id))
        db.commit()
