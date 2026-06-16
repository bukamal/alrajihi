# -*- coding: utf-8 -*-
"""Enterprise RBAC service (Phase 157).

Provides a database-backed roles/permissions layer while preserving the legacy
`users.role` field as a compatibility fallback.  All methods are defensive so
permission checks never crash the UI if a migration is still pending.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Dict, Optional

from auth.session import UserSession


DEFAULT_ROLE_PERMISSIONS = {
    'admin': None,  # all permissions
    'manager': {
        'reports.view', 'reports.export', 'invoices.edit', 'returns.edit',
        'branches.view_all', 'approval.submit', 'approval.approve', 'approval.reject'
    },
    'accountant': {
        'reports.view', 'reports.export', 'accounting.view', 'accounting.post',
        'accounting.close_period', 'approval.submit'
    },
    'cashier': {'approval.submit'},
    'viewer': {'reports.view'},
}

ACTION_PERMISSION_MAP = {
    'hide_profit': 'reports.view',
    'delete_records': 'invoices.delete',
    'edit_invoices': 'invoices.edit',
    'edit_returns': 'returns.edit',
    'view_reports': 'reports.view',
    'export_reports': 'reports.export',
    'view_all_branches': 'branches.view_all',
    'manage_all_branches': 'branches.manage_all',
    'approval.submit': 'approval.submit',
    'approval.approve': 'approval.approve',
    'approval.reject': 'approval.reject',
    'accounting.view': 'accounting.view',
    'accounting.post': 'accounting.post',
    'accounting.close_period': 'accounting.close_period',
    'settings.manage': 'settings.manage',
    'users.manage': 'users.manage',
    'system.health.view': 'system.health.view',
    'system.validation.run': 'system.validation.run',
    'approval.matrix.manage': 'approval.matrix.manage',
    'approval.level1': 'approval.level1',
    'approval.level2': 'approval.level2',
    'approval.level3': 'approval.level3',
}


class RBACService:
    def _conn(self):
        from database.connection import DatabaseConnection
        db = DatabaseConnection()
        if db.is_remote():
            return None
        return db.get_connection()

    def _user_id(self, user_id: str | None = None) -> str | None:
        return str(user_id or UserSession.get_current_user_id() or '') or None

    def _legacy_role(self, user_id: str | None = None) -> str:
        current = UserSession.get_current() or {}
        if user_id is None and current.get('role'):
            return str(current.get('role')).lower()
        try:
            conn = self._conn()
            if not conn or not user_id:
                return 'admin'
            row = conn.execute('SELECT role FROM users WHERE id=?', (str(user_id),)).fetchone()
            return str(row['role'] if row else 'user').lower()
        except Exception:
            return 'admin'

    def list_roles(self) -> List[Dict]:
        try:
            conn = self._conn()
            if not conn:
                return []
            return [dict(r) for r in conn.execute('SELECT * FROM roles ORDER BY is_system DESC, name').fetchall()]
        except Exception:
            return []

    def list_permissions(self) -> List[Dict]:
        try:
            conn = self._conn()
            if not conn:
                return []
            return [dict(r) for r in conn.execute('SELECT * FROM permissions ORDER BY module, key').fetchall()]
        except Exception:
            return []

    def user_roles(self, user_id: str | None = None) -> List[str]:
        uid = self._user_id(user_id)
        try:
            conn = self._conn()
            if not conn or not uid:
                return [self._legacy_role(user_id)]
            rows = conn.execute('''
                SELECT r.name FROM user_roles ur JOIN roles r ON r.id=ur.role_id
                WHERE ur.user_id=? AND r.is_active=1
            ''', (uid,)).fetchall()
            roles = [str(r['name']).lower() for r in rows]
            if roles:
                return roles
        except Exception:
            pass
        return [self._legacy_role(user_id)]


    def role_parent_map(self) -> dict[str, str]:
        try:
            conn = self._conn()
            if not conn:
                return {}
            rows = conn.execute("""
                SELECT r.name AS role_name, p.name AS parent_name
                FROM roles r LEFT JOIN roles p ON p.id=r.parent_role_id
                WHERE r.is_active=1
            """).fetchall()
            return {str(r['role_name']).lower(): str(r['parent_name']).lower() for r in rows if r['parent_name']}
        except Exception:
            return {}

    def effective_user_roles(self, user_id: str | None = None) -> List[str]:
        roles = [str(r).lower() for r in self.user_roles(user_id)]
        parent_map = self.role_parent_map()
        seen = set(roles)
        stack = list(roles)
        while stack:
            role = stack.pop()
            parent = parent_map.get(role)
            if parent and parent not in seen:
                seen.add(parent)
                stack.append(parent)
        return sorted(seen)

    def role_permissions(self, role_name: str) -> set[str]:
        try:
            conn = self._conn()
            if not conn:
                defaults = DEFAULT_ROLE_PERMISSIONS.get(str(role_name).lower(), set())
                return {'*'} if defaults is None else set(defaults)
            row = conn.execute('SELECT id FROM roles WHERE name=? AND is_active=1', (str(role_name).lower(),)).fetchone()
            if not row:
                return set()
            rows = conn.execute('SELECT permission_key FROM role_permissions WHERE role_id=? AND allowed=1', (row['id'],)).fetchall()
            return {str(r['permission_key']) for r in rows}
        except Exception:
            defaults = DEFAULT_ROLE_PERMISSIONS.get(str(role_name).lower(), set())
            return {'*'} if defaults is None else set(defaults)

    def can_access_branch(self, branch_id: int | None, user_id: str | None = None) -> bool:
        if branch_id in (None, '', 0):
            return True
        if self.has_permission('branches.view_all', user_id):
            return True
        allowed = self.allowed_branch_ids(user_id)
        try:
            return int(branch_id) in allowed
        except Exception:
            return False


    def user_permissions(self, user_id: str | None = None) -> set[str]:
        roles = self.effective_user_roles(user_id)
        if 'admin' in roles:
            return {p['key'] for p in self.list_permissions()} or {'*'}
        perms: set[str] = set()
        try:
            conn = self._conn()
            uid = self._user_id(user_id)
            if conn and uid:
                rows = conn.execute('''
                    SELECT rp.permission_key FROM user_roles ur
                    JOIN role_permissions rp ON rp.role_id=ur.role_id AND rp.allowed=1
                    JOIN roles r ON r.id=ur.role_id AND r.is_active=1
                    WHERE ur.user_id=?
                ''', (uid,)).fetchall()
                perms.update(str(r['permission_key']) for r in rows)
        except Exception:
            pass
        if not perms:
            for role in roles:
                defaults = DEFAULT_ROLE_PERMISSIONS.get(role, set())
                if defaults is None:
                    return {'*'}
                perms.update(defaults)
        return perms

    def has_permission(self, permission_key: str, user_id: str | None = None) -> bool:
        key = ACTION_PERMISSION_MAP.get(permission_key, permission_key)
        perms = self.user_permissions(user_id)
        return '*' in perms or key in perms

    def can_action(self, action: str, user_id: str | None = None) -> bool:
        return self.has_permission(ACTION_PERMISSION_MAP.get(action, action), user_id)

    def assign_roles(self, user_id: str, role_names: Iterable[str]) -> bool:
        conn = self._conn()
        if not conn:
            return False
        role_names = [str(r).strip().lower() for r in role_names if str(r).strip()]
        conn.execute('DELETE FROM user_roles WHERE user_id=?', (str(user_id),))
        for name in role_names:
            row = conn.execute('SELECT id FROM roles WHERE name=?', (name,)).fetchone()
            if row:
                conn.execute('INSERT OR IGNORE INTO user_roles(user_id, role_id) VALUES (?,?)', (str(user_id), row['id']))
        conn.commit()
        return True

    def set_role_permissions(self, role_name: str, permission_keys: Iterable[str]) -> bool:
        conn = self._conn()
        if not conn:
            return False
        role = conn.execute('SELECT id FROM roles WHERE name=?', (str(role_name).strip().lower(),)).fetchone()
        if not role:
            return False
        role_id = role['id']
        conn.execute('DELETE FROM role_permissions WHERE role_id=?', (role_id,))
        for key in permission_keys:
            if conn.execute('SELECT 1 FROM permissions WHERE key=?', (str(key),)).fetchone():
                conn.execute('INSERT OR REPLACE INTO role_permissions(role_id, permission_key, allowed) VALUES (?,?,1)', (role_id, str(key)))
        conn.commit()
        return True

    def set_user_branches(self, user_id: str, branch_ids: Iterable[int]) -> bool:
        conn = self._conn()
        if not conn:
            return False
        conn.execute('DELETE FROM user_branch_access WHERE user_id=?', (str(user_id),))
        for bid in branch_ids:
            try:
                conn.execute('INSERT OR IGNORE INTO user_branch_access(user_id, branch_id) VALUES (?,?)', (str(user_id), int(bid)))
            except Exception:
                continue
        conn.commit()
        return True

    def allowed_branch_ids(self, user_id: str | None = None) -> List[int]:
        uid = self._user_id(user_id)
        try:
            conn = self._conn()
            if not conn or not uid:
                return []
            rows = conn.execute('SELECT branch_id FROM user_branch_access WHERE user_id=?', (uid,)).fetchall()
            return [int(r['branch_id']) for r in rows]
        except Exception:
            return []


rbac_service = RBACService()
