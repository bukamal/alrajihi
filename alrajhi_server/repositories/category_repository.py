from __future__ import annotations

import datetime
from typing import Any

from alrajhi_server.database.connection import get_db


class CategoryRepository:
    """Server-side repository for category tree data."""

    @staticmethod
    def _normalize_parent(parent_id: Any) -> int | None:
        if parent_id in (None, '', 0, '0'):
            return None
        return int(parent_id)

    @staticmethod
    def _category_dicts(rows: list[Any]) -> list[dict[str, Any]]:
        cats = [dict(row) for row in rows]
        by_id = {c['id']: c for c in cats}
        for c in cats:
            names = [c.get('name') or '']
            parent_id = c.get('parent_id')
            guard: set[int] = set()
            while parent_id and parent_id in by_id and parent_id not in guard:
                guard.add(parent_id)
                parent = by_id[parent_id]
                names.insert(0, parent.get('name') or '')
                parent_id = parent.get('parent_id')
            c['full_name'] = ' / '.join([x for x in names if x])
            c['status_text'] = 'نشط' if int(c.get('is_active') or 0) == 1 and not c.get('deleted_at') else 'مؤرشف'
        return cats

    def get_by_id(self, category_id: int, user_id: Any):
        return get_db().execute('''
            SELECT c.*, p.name AS parent_name,
                   (SELECT COUNT(*) FROM items i WHERE i.category_id = c.id AND i.user_id = c.user_id AND COALESCE(i.deleted_at, '') = '') AS item_count,
                   (SELECT COUNT(*) FROM categories ch WHERE ch.parent_id = c.id AND ch.user_id = c.user_id AND COALESCE(ch.deleted_at, '') = '') AS child_count
            FROM categories c
            LEFT JOIN categories p ON p.id = c.parent_id
            WHERE c.id = ? AND c.user_id = ?
        ''', (category_id, user_id)).fetchone()

    def _validate(self, user_id: Any, name: str | None, parent_id: Any = None, category_id: int | None = None) -> tuple[str, int | None]:
        db = get_db()
        name = (name or '').strip()
        if not name:
            raise ValueError('اسم التصنيف مطلوب')
        parent_id = self._normalize_parent(parent_id)
        if category_id and parent_id == int(category_id):
            raise ValueError('لا يمكن أن يكون التصنيف أباً لنفسه')
        if parent_id:
            parent = self.get_by_id(parent_id, user_id)
            if not parent or parent['deleted_at']:
                raise ValueError('التصنيف الأب غير موجود أو مؤرشف')
            current = parent['parent_id']
            guard: set[int] = set()
            while current and current not in guard:
                if category_id and int(current) == int(category_id):
                    raise ValueError('لا يمكن إنشاء حلقة في شجرة التصنيفات')
                guard.add(current)
                p = self.get_by_id(current, user_id)
                current = p['parent_id'] if p else None
        dup = db.execute('''
            SELECT id FROM categories
            WHERE user_id = ? AND name = ? AND COALESCE(parent_id, 0) = COALESCE(?, 0)
              AND COALESCE(deleted_at, '') = ''
              AND (? IS NULL OR id <> ?)
        ''', (user_id, name, parent_id, category_id, category_id)).fetchone()
        if dup:
            raise ValueError('يوجد تصنيف بنفس الاسم ضمن نفس المستوى')
        return name, parent_id

    def list(self, user_id: Any, search: str | None = None, include_inactive: bool = False, include_deleted: bool = False) -> list[dict[str, Any]]:
        db = get_db()
        query = '''
            SELECT c.*, p.name AS parent_name,
                   (SELECT COUNT(*) FROM items i WHERE i.category_id = c.id AND i.user_id = c.user_id AND COALESCE(i.deleted_at, '') = '') AS item_count,
                   (SELECT COUNT(*) FROM categories ch WHERE ch.parent_id = c.id AND ch.user_id = c.user_id AND COALESCE(ch.deleted_at, '') = '') AS child_count
            FROM categories c
            LEFT JOIN categories p ON p.id = c.parent_id
            WHERE c.user_id = ?
        '''
        params: list[Any] = [user_id]
        if not include_deleted:
            query += " AND COALESCE(c.deleted_at, '') = ''"
        if not include_inactive:
            query += " AND COALESCE(c.is_active, 1) = 1"
        if search:
            query += " AND (c.name LIKE ? OR COALESCE(c.description, '') LIKE ? OR COALESCE(p.name, '') LIKE ?)"
            like = f'%{search}%'
            params.extend([like, like, like])
        query += " ORDER BY COALESCE(p.name, ''), c.name"
        rows = db.execute(query, params).fetchall()
        return self._category_dicts(rows)

    def create(self, user_id: Any, data: dict[str, Any]) -> int:
        db = get_db()
        name, parent_id = self._validate(user_id, data.get('name'), data.get('parent_id'))
        cur = db.execute('''
            INSERT INTO categories (user_id, name, parent_id, description, color, icon, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, name, parent_id, data.get('description', '') or '', data.get('color', '#64748B') or '#64748B', data.get('icon', 'folder') or 'folder', 1 if data.get('is_active', 1) else 0))
        db.commit()
        return int(cur.lastrowid)

    def update(self, category_id: int, user_id: Any, data: dict[str, Any]) -> None:
        db = get_db()
        name, parent_id = self._validate(user_id, data.get('name'), data.get('parent_id'), category_id)
        db.execute('''
            UPDATE categories
            SET name=?, parent_id=?, description=?, color=?, icon=?, is_active=?
            WHERE id=? AND user_id=?
        ''', (name, parent_id, data.get('description', '') or '', data.get('color', '#64748B') or '#64748B', data.get('icon', 'folder') or 'folder', 1 if data.get('is_active', 1) else 0, category_id, user_id))
        db.commit()

    def delete(self, category_id: int, user_id: Any) -> None:
        db = get_db()
        if db.execute("SELECT id FROM items WHERE category_id=? AND user_id=? AND COALESCE(deleted_at, '') = '' LIMIT 1", (category_id, user_id)).fetchone():
            raise ValueError('لا يمكن حذف التصنيف لوجود مواد مرتبطة به')
        if db.execute("SELECT id FROM categories WHERE parent_id=? AND user_id=? AND COALESCE(deleted_at, '') = '' LIMIT 1", (category_id, user_id)).fetchone():
            raise ValueError('لا يمكن حذف التصنيف لوجود تصنيفات فرعية')
        db.execute("UPDATE categories SET deleted_at=?, is_active=0 WHERE id=? AND user_id=?", (datetime.datetime.now().isoformat(), category_id, user_id))
        db.commit()

    def restore(self, category_id: int, user_id: Any) -> None:
        db = get_db()
        db.execute("UPDATE categories SET deleted_at=NULL, is_active=1 WHERE id=? AND user_id=?", (category_id, user_id))
        db.commit()
