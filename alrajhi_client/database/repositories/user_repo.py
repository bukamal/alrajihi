# -*- coding: utf-8 -*-
from database.repositories.base_repo import BaseRepository
from auth.password import hash_password, verify_password
from auth.session import UserSession
import datetime
from typing import List, Dict, Optional

class UserRepository(BaseRepository):
    def get_all(self) -> List[Dict]:
        if self.db.is_remote():
            return self.db.get_rest_client().get_users()
        else:
            return self._fetch_all("SELECT u.id, u.username, u.full_name, u.role, u.branch_id, b.name AS branch_name, u.created_at, u.last_login, u.force_password_change FROM users u LEFT JOIN branches b ON b.id=u.branch_id ORDER BY u.id")

    def get_by_id(self, user_id: str) -> Optional[Dict]:
        if self.db.is_remote():
            users = self.get_all()
            for u in users:
                if u['id'] == user_id:
                    return u
            return None
        else:
            return self._fetch_one("SELECT * FROM users WHERE id=?", (user_id,))

    def get_by_username(self, username: str) -> Optional[Dict]:
        if self.db.is_remote():
            users = self.get_all()
            for u in users:
                if u['username'] == username:
                    return u
            return None
        else:
            return self._fetch_one("SELECT * FROM users WHERE username=?", (username,))

    def authenticate(self, username: str, password: str) -> Optional[Dict]:
        if self.db.is_remote():
            raise NotImplementedError("Use RestClient.login() for remote mode")
        user = self.get_by_username(username)
        if user and verify_password(password, user['password_hash'], user['salt']):
            now = datetime.datetime.now().isoformat()
            self._execute("UPDATE users SET last_login=? WHERE id=?", (now, user['id']))
            self._commit()
            return user
        return None

    def create(self, username: str, password: str, full_name: str, role: str, branch_id=None) -> str:
        if self.db.is_remote():
            data = {
                'username': username,
                'password': password,
                'full_name': full_name,
                'role': role,
                'branch_id': branch_id
            }
            user_id = str(self.db.get_rest_client().add_user(data))
            try:
                self.db.get_rest_client().set_user_roles(user_id, [role])
            except Exception:
                pass
            return user_id
        else:
            pwd_hash, salt = hash_password(password)
            now = datetime.datetime.now().isoformat()
            user_id = f"user_{int(datetime.datetime.now().timestamp())}"
            self._execute('''
                INSERT INTO users (id, username, password_hash, salt, full_name, role, branch_id, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, username, pwd_hash, salt, full_name, role, branch_id, now))
            self._commit()
            self._sync_rbac_role(user_id, role, branch_id)
            current = UserSession.get_current()
            if current:
                self.db._log_audit_local(
                    current.get('id'),
                    current.get('username'),
                    "إضافة مستخدم",
                    'users', user_id, f"المستخدم: {username}"
                )
            return user_id

    def update(self, user_id: str, full_name: str, role: str, branch_id=None):
        if self.db.is_remote():
            data = {'full_name': full_name, 'role': role, 'branch_id': branch_id}
            self.db.get_rest_client().update_user(int(user_id), data)
            try:
                self.db.get_rest_client().set_user_roles(str(user_id), [role])
            except Exception:
                pass
        else:
            self._execute('UPDATE users SET full_name=?, role=?, branch_id=? WHERE id=?', (full_name, role, branch_id, user_id))
            self._commit()
            self._sync_rbac_role(user_id, role, branch_id)
            current = UserSession.get_current()
            if current:
                self.db._log_audit_local(
                    current.get('id'),
                    current.get('username'),
                    "تعديل مستخدم",
                    'users', user_id, f"الاسم: {full_name}, صلاحية: {role}"
                )

    def _sync_rbac_role(self, user_id: str, role: str, branch_id=None):
        """Keep legacy users.role, user_roles, and user_branch_access aligned."""
        try:
            conn = self.db.get_connection()
            role_name = str(role or 'viewer').lower()
            row = conn.execute('SELECT id FROM roles WHERE name=?', (role_name,)).fetchone()
            if row:
                conn.execute('DELETE FROM user_roles WHERE user_id=?', (str(user_id),))
                conn.execute('INSERT OR IGNORE INTO user_roles(user_id, role_id, branch_id) VALUES (?,?,?)', (str(user_id), row['id'], branch_id))
            if branch_id is not None:
                conn.execute('DELETE FROM user_branch_access WHERE user_id=?', (str(user_id),))
                conn.execute('INSERT OR IGNORE INTO user_branch_access(user_id, branch_id) VALUES (?,?)', (str(user_id), branch_id))
            conn.commit()
        except Exception:
            pass

    def change_password(self, user_id: str, old_password: str, new_password: str) -> bool:
        if self.db.is_remote():
            try:
                self.db.get_rest_client().change_password(old_password, new_password)
                return True
            except:
                return False
        else:
            user = self.get_by_id(user_id)
            if not user or not verify_password(old_password, user['password_hash'], user['salt']):
                return False
            new_hash, new_salt = hash_password(new_password)
            self._execute('UPDATE users SET password_hash=?, salt=?, force_password_change=0 WHERE id=?',
                         (new_hash, new_salt, user_id))
            self._commit()
            current = UserSession.get_current()
            if current:
                self.db._log_audit_local(
                    current.get('id'),
                    current.get('username'),
                    "تغيير كلمة المرور",
                    'users', user_id, ""
                )
            return True

    def delete(self, user_id: str) -> bool:
        if self.db.is_remote():
            if user_id == "1":
                return False
            try:
                self.db.get_rest_client().delete_user(int(user_id))
                return True
            except:
                return False
        else:
            if user_id == 'admin':
                return False
            user = self.get_by_id(user_id)
            self._execute('DELETE FROM users WHERE id=?', (user_id,))
            self._commit()
            current = UserSession.get_current()
            if current:
                self.db._log_audit_local(
                    current.get('id'),
                    current.get('username'),
                    "حذف مستخدم",
                    'users', user_id, f"المستخدم: {user['username'] if user else ''}"
                )
            return True

    def set_force_password_change(self, user_id: str, force: bool):
        if self.db.is_remote():
            # قد لا يكون مدعوماً في وضع العميل
            pass
        else:
            old = self.get_by_id(user_id)
            val = 1 if force else 0
            self._execute("UPDATE users SET force_password_change=? WHERE id=?", (val, user_id))
            self._commit()
            try:
                from core.services.audit_service import audit_service
                audit_service.log('UPDATE', 'USER', None, old_values=old, new_values=self.get_by_id(user_id), details='تعديل إلزام تغيير كلمة المرور')
            except Exception:
                pass


