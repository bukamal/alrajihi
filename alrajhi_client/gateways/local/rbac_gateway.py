# -*- coding: utf-8 -*-
"""Local RBAC gateway adapter."""
from __future__ import annotations

from typing import Dict, Iterable, List

from gateways.rbac_gateway import RBACGateway


class LocalRBACGateway(RBACGateway):
    def __init__(self, conn):
        self.conn = conn

    def legacy_role(self, user_id: str | None = None) -> str:
        if not user_id:
            return "admin"
        row = self.conn.execute('SELECT role FROM users WHERE id=?', (str(user_id),)).fetchone()
        return str(row['role'] if row else 'user').lower()

    def list_roles(self) -> List[Dict]:
        return [dict(r) for r in self.conn.execute('SELECT * FROM roles ORDER BY is_system DESC, name').fetchall()]

    def list_permissions(self) -> List[Dict]:
        return [dict(r) for r in self.conn.execute('SELECT * FROM permissions ORDER BY module, key').fetchall()]

    def user_roles(self, user_id: str | None = None) -> List[str]:
        if not user_id:
            return []
        rows = self.conn.execute('''
            SELECT r.name FROM user_roles ur JOIN roles r ON r.id=ur.role_id
            WHERE ur.user_id=? AND r.is_active=1
        ''', (str(user_id),)).fetchall()
        return [str(r['name']).lower() for r in rows]

    def role_parent_map(self) -> dict[str, str]:
        rows = self.conn.execute("""
            SELECT r.name AS role_name, p.name AS parent_name
            FROM roles r LEFT JOIN roles p ON p.id=r.parent_role_id
            WHERE r.is_active=1
        """).fetchall()
        return {str(r['role_name']).lower(): str(r['parent_name']).lower() for r in rows if r['parent_name']}

    def role_permissions(self, role_name: str) -> set[str]:
        row = self.conn.execute('SELECT id FROM roles WHERE name=? AND is_active=1', (str(role_name).lower(),)).fetchone()
        if not row:
            return set()
        rows = self.conn.execute('SELECT permission_key FROM role_permissions WHERE role_id=? AND allowed=1', (row['id'],)).fetchall()
        return {str(r['permission_key']) for r in rows}

    def user_direct_permissions(self, user_id: str | None = None) -> set[str]:
        if not user_id:
            return set()
        rows = self.conn.execute('''
            SELECT rp.permission_key FROM user_roles ur
            JOIN role_permissions rp ON rp.role_id=ur.role_id AND rp.allowed=1
            JOIN roles r ON r.id=ur.role_id AND r.is_active=1
            WHERE ur.user_id=?
        ''', (str(user_id),)).fetchall()
        return {str(r['permission_key']) for r in rows}

    def assign_roles(self, user_id: str, role_names: Iterable[str]) -> bool:
        names = [str(r).strip().lower() for r in role_names if str(r).strip()]
        self.conn.execute('DELETE FROM user_roles WHERE user_id=?', (str(user_id),))
        for name in names:
            row = self.conn.execute('SELECT id FROM roles WHERE name=?', (name,)).fetchone()
            if row:
                self.conn.execute('INSERT OR IGNORE INTO user_roles(user_id, role_id) VALUES (?,?)', (str(user_id), row['id']))
        self.conn.commit()
        return True

    def set_role_permissions(self, role_name: str, permission_keys: Iterable[str]) -> bool:
        role = self.conn.execute('SELECT id FROM roles WHERE name=?', (str(role_name).strip().lower(),)).fetchone()
        if not role:
            return False
        role_id = role['id']
        self.conn.execute('DELETE FROM role_permissions WHERE role_id=?', (role_id,))
        for key in permission_keys:
            if self.conn.execute('SELECT 1 FROM permissions WHERE key=?', (str(key),)).fetchone():
                self.conn.execute('INSERT OR REPLACE INTO role_permissions(role_id, permission_key, allowed) VALUES (?,?,1)', (role_id, str(key)))
        self.conn.commit()
        return True

    def set_user_branches(self, user_id: str, branch_ids: Iterable[int]) -> bool:
        self.conn.execute('DELETE FROM user_branch_access WHERE user_id=?', (str(user_id),))
        for bid in branch_ids:
            try:
                self.conn.execute('INSERT OR IGNORE INTO user_branch_access(user_id, branch_id) VALUES (?,?)', (str(user_id), int(bid)))
            except Exception:
                continue
        self.conn.commit()
        return True

    def allowed_branch_ids(self, user_id: str | None = None) -> List[int]:
        if not user_id:
            return []
        rows = self.conn.execute('SELECT branch_id FROM user_branch_access WHERE user_id=?', (str(user_id),)).fetchall()
        return [int(r['branch_id']) for r in rows]
