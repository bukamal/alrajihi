# -*- coding: utf-8 -*-
from __future__ import annotations

import datetime
from typing import Dict, List, Optional

from database.repositories.base_repo import BaseRepository
from auth.session import UserSession

DEFAULT_BRANCH_NAME = 'الفرع الرئيسي'
DEFAULT_BRANCH_CODE = 'MAIN'


class BranchRepository(BaseRepository):
    """Core branch repository."""

    def _now(self) -> str:
        return datetime.datetime.now().isoformat()

    def _uid(self) -> str:
        return UserSession.get_current_user_id() or 'admin'

    def ensure_schema(self) -> None:
        if self.db.is_remote():
            return
        conn = self.db.get_connection()
        conn.execute('PRAGMA foreign_keys=ON')
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS branches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                name TEXT NOT NULL,
                code TEXT,
                address TEXT,
                phone TEXT,
                notes TEXT,
                is_default INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                deleted_at TEXT,
                created_at TEXT,
                updated_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id),
                UNIQUE(user_id, name),
                UNIQUE(user_id, code)
            );
            CREATE INDEX IF NOT EXISTS idx_branches_user ON branches(user_id);
            CREATE INDEX IF NOT EXISTS idx_branches_active ON branches(user_id, deleted_at, is_active);
        """)
        try:
            conn.execute("ALTER TABLE warehouses ADD COLUMN branch_id INTEGER")
        except Exception:
            pass
        try:
            conn.execute("CREATE INDEX IF NOT EXISTS idx_warehouses_branch ON warehouses(branch_id)")
        except Exception:
            pass
        conn.commit()

    def bootstrap_defaults(self) -> None:
        if self.db.is_remote():
            return
        self.ensure_schema()
        conn = self.db.get_connection()
        now = self._now()
        users = conn.execute("""
            SELECT id FROM users
            UNION
            SELECT DISTINCT user_id AS id FROM warehouses WHERE user_id IS NOT NULL
            UNION
            SELECT DISTINCT user_id AS id FROM items WHERE user_id IS NOT NULL
        """).fetchall()
        for user in users:
            uid = user['id']
            if not uid:
                continue
            row = conn.execute(
                "SELECT id FROM branches WHERE user_id=? AND is_default=1 AND deleted_at IS NULL LIMIT 1",
                (uid,)
            ).fetchone()
            if row:
                branch_id = row['id']
            else:
                cur = conn.execute("""
                    INSERT OR IGNORE INTO branches
                    (user_id, name, code, address, phone, notes, is_default, is_active, created_at, updated_at)
                    VALUES (?, ?, ?, '', '', ?, 1, 1, ?, ?)
                """, (uid, DEFAULT_BRANCH_NAME, DEFAULT_BRANCH_CODE, 'تم إنشاؤه تلقائياً عند تفعيل نظام الفروع', now, now))
                found = conn.execute(
                    "SELECT id FROM branches WHERE user_id=? AND name=? LIMIT 1",
                    (uid, DEFAULT_BRANCH_NAME)
                ).fetchone()
                branch_id = cur.lastrowid or (found['id'] if found else None)
            if branch_id:
                try:
                    conn.execute("UPDATE warehouses SET branch_id=? WHERE user_id=? AND branch_id IS NULL", (branch_id, uid))
                except Exception:
                    pass
        conn.commit()

    def default_branch_id(self, user_id: str | None = None) -> Optional[int]:
        if self.db.is_remote():
            return self.db.get_rest_client().default_branch_id()
        self.bootstrap_defaults()
        uid = user_id or self._uid()
        row = self.db.get_connection().execute(
            "SELECT id FROM branches WHERE user_id=? AND is_default=1 AND deleted_at IS NULL LIMIT 1",
            (uid,)
        ).fetchone()
        return int(row['id']) if row else None

    def list_branches(self, include_archived: bool = False) -> List[Dict]:
        if self.db.is_remote():
            return self.db.get_rest_client().get_branches(include_archived)
        self.bootstrap_defaults()
        uid = self._uid()
        sql = """
            SELECT b.*, COUNT(DISTINCT w.id) AS warehouse_count
            FROM branches b
            LEFT JOIN warehouses w ON w.branch_id=b.id AND w.user_id=b.user_id AND w.deleted_at IS NULL
            WHERE b.user_id=?
        """
        params = [uid]
        if not include_archived:
            sql += " AND b.deleted_at IS NULL AND COALESCE(b.is_active, 1)=1"
        sql += " GROUP BY b.id ORDER BY b.is_default DESC, b.name"
        return [dict(r) for r in self.db.get_connection().execute(sql, params).fetchall()]

    def get_by_id(self, branch_id: int) -> Optional[Dict]:
        if self.db.is_remote():
            return self.db.get_rest_client().get_branch(branch_id)
        self.bootstrap_defaults()
        uid = self._uid()
        row = self.db.get_connection().execute("SELECT * FROM branches WHERE id=? AND user_id=?", (branch_id, uid)).fetchone()
        return dict(row) if row else None

    def add(self, data: Dict) -> int:
        if self.db.is_remote():
            return self.db.get_rest_client().add_branch(data)
        self.bootstrap_defaults()
        uid = self._uid()
        payload = self._validate(data)
        now = self._now()
        cur = self.db.get_connection().execute("""
            INSERT INTO branches (user_id, name, code, address, phone, notes, is_default, is_active, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, 0, 1, ?, ?)
        """, (uid, payload['name'], payload['code'], payload['address'], payload['phone'], payload['notes'], now, now))
        self.db.get_connection().commit()
        return int(cur.lastrowid)

    def update(self, branch_id: int, data: Dict) -> None:
        if self.db.is_remote():
            return self.db.get_rest_client().update_branch(branch_id, data)
        self.bootstrap_defaults()
        uid = self._uid()
        payload = self._validate(data)
        conn = self.db.get_connection()
        row = conn.execute("SELECT is_default FROM branches WHERE id=? AND user_id=?", (branch_id, uid)).fetchone()
        if not row:
            raise ValueError('الفرع غير موجود')
        conn.execute("""
            UPDATE branches
            SET name=?, code=?, address=?, phone=?, notes=?, is_active=?, updated_at=?
            WHERE id=? AND user_id=?
        """, (payload['name'], payload['code'], payload['address'], payload['phone'], payload['notes'], payload['is_active'], self._now(), branch_id, uid))
        conn.commit()

    def archive(self, branch_id: int) -> None:
        if self.db.is_remote():
            return self.db.get_rest_client().archive_branch(branch_id)
        self.bootstrap_defaults()
        uid = self._uid()
        conn = self.db.get_connection()
        branch = conn.execute("SELECT is_default FROM branches WHERE id=? AND user_id=?", (branch_id, uid)).fetchone()
        if not branch:
            raise ValueError('الفرع غير موجود')
        if int(branch['is_default'] or 0) == 1:
            raise ValueError('لا يمكن أرشفة الفرع الرئيسي')
        wh = conn.execute("SELECT COUNT(*) AS c FROM warehouses WHERE branch_id=? AND deleted_at IS NULL", (branch_id,)).fetchone()
        if wh and int(wh['c'] or 0) > 0:
            raise ValueError('لا يمكن أرشفة فرع مرتبط بمستودعات نشطة. انقل أو أرشف المستودعات أولاً.')
        now = self._now()
        conn.execute("UPDATE branches SET deleted_at=?, is_active=0, updated_at=? WHERE id=? AND user_id=?", (now, now, branch_id, uid))
        conn.commit()

    def _validate(self, data: Dict) -> Dict:
        payload = dict(data or {})
        name = str(payload.get('name', '')).strip()
        if not name:
            raise ValueError('اسم الفرع مطلوب')
        code = str(payload.get('code', '')).strip().upper()
        return {
            'name': name,
            'code': code,
            'address': str(payload.get('address', '')).strip(),
            'phone': str(payload.get('phone', '')).strip(),
            'notes': str(payload.get('notes', '')).strip(),
            'is_active': 1 if payload.get('is_active', 1) else 0,
        }
