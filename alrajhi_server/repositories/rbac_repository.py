from __future__ import annotations

from alrajhi_server.database.connection import get_db


class RBACRepository:
    """Server-side RBAC persistence boundary for Flask API routes."""

    def __init__(self) -> None:
        self._db = get_db()

    def is_admin(self, user_id: str) -> bool:
        row = self._db.execute('SELECT role FROM users WHERE id=?', (str(user_id),)).fetchone()
        return bool(row and row['role'] == 'admin')

    def ensure_user_role_compat(self, user_id: str) -> None:
        self._db.execute('''
            INSERT OR IGNORE INTO user_roles(user_id, role_id)
            SELECT u.id, r.id FROM users u JOIN roles r ON lower(COALESCE(u.role,'user'))=r.name WHERE u.id=?
        ''', (str(user_id),))
        self._db.commit()

    def list_user_role_names(self, user_id: str) -> list[str]:
        self.ensure_user_role_compat(user_id)
        return [r['name'] for r in self._db.execute('''
            SELECT r.name FROM user_roles ur JOIN roles r ON r.id=ur.role_id
            WHERE ur.user_id=? AND r.is_active=1
        ''', (str(user_id),)).fetchall()]

    def list_user_permissions(self, user_id: str) -> list[str]:
        roles = self.list_user_role_names(user_id)
        if 'admin' in roles:
            return [r['key'] for r in self._db.execute('SELECT key FROM permissions ORDER BY key').fetchall()]
        return [r['permission_key'] for r in self._db.execute('''
            SELECT DISTINCT rp.permission_key FROM user_roles ur
            JOIN role_permissions rp ON rp.role_id=ur.role_id AND rp.allowed=1
            JOIN roles r ON r.id=ur.role_id AND r.is_active=1
            WHERE ur.user_id=? ORDER BY rp.permission_key
        ''', (str(user_id),)).fetchall()]

    def list_roles(self) -> list[dict]:
        return [dict(r) for r in self._db.execute('SELECT * FROM roles ORDER BY is_system DESC, name').fetchall()]

    def list_permissions(self) -> list[dict]:
        return [dict(r) for r in self._db.execute('SELECT * FROM permissions ORDER BY module, key').fetchall()]

    def list_user_branch_ids(self, user_id: str) -> list[int]:
        return [r['branch_id'] for r in self._db.execute('SELECT branch_id FROM user_branch_access WHERE user_id=?', (str(user_id),)).fetchall()]

    def list_user_roles(self, user_id: str) -> list[dict]:
        self.ensure_user_role_compat(user_id)
        rows = self._db.execute('''
            SELECT r.* FROM user_roles ur JOIN roles r ON r.id=ur.role_id WHERE ur.user_id=? ORDER BY r.name
        ''', (str(user_id),)).fetchall()
        return [dict(r) for r in rows]

    def replace_user_roles(self, user_id: str, role_names: list[str]) -> None:
        self._db.execute('DELETE FROM user_roles WHERE user_id=?', (str(user_id),))
        for name in role_names:
            role = self._db.execute('SELECT id FROM roles WHERE name=?', (name,)).fetchone()
            if role:
                self._db.execute('INSERT OR IGNORE INTO user_roles(user_id, role_id) VALUES (?,?)', (str(user_id), role['id']))
        self._db.commit()

    def list_role_permissions(self, role_name: str) -> list[dict]:
        rows = self._db.execute('''
            SELECT p.*, COALESCE(rp.allowed,0) AS allowed FROM permissions p
            LEFT JOIN roles r ON r.name=?
            LEFT JOIN role_permissions rp ON rp.role_id=r.id AND rp.permission_key=p.key
            ORDER BY p.module, p.key
        ''', (str(role_name).lower(),)).fetchall()
        return [dict(r) for r in rows]

    def replace_role_permissions(self, role_name: str, permission_keys: list[str]) -> bool:
        role = self._db.execute('SELECT id FROM roles WHERE name=?', (str(role_name).strip().lower(),)).fetchone()
        if not role:
            return False
        self._db.execute('DELETE FROM role_permissions WHERE role_id=?', (role['id'],))
        for key in permission_keys:
            if self._db.execute('SELECT 1 FROM permissions WHERE key=?', (key,)).fetchone():
                self._db.execute('INSERT OR REPLACE INTO role_permissions(role_id, permission_key, allowed) VALUES (?,?,1)', (role['id'], key))
        self._db.commit()
        return True

    def list_user_branches(self, user_id: str) -> list[dict]:
        rows = self._db.execute('''
            SELECT b.* FROM user_branch_access uba JOIN branches b ON b.id=uba.branch_id WHERE uba.user_id=? ORDER BY b.name
        ''', (str(user_id),)).fetchall()
        return [dict(r) for r in rows]

    def replace_user_branches(self, user_id: str, branch_ids: list) -> None:
        self._db.execute('DELETE FROM user_branch_access WHERE user_id=?', (str(user_id),))
        for bid in branch_ids:
            try:
                self._db.execute('INSERT OR IGNORE INTO user_branch_access(user_id, branch_id) VALUES (?,?)', (str(user_id), int(bid)))
            except Exception:
                continue
        self._db.commit()


def get_rbac_repository() -> RBACRepository:
    return RBACRepository()
