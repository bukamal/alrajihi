# -*- coding: utf-8 -*-
from __future__ import annotations

import datetime
from typing import Dict, Optional

from database.connection import DatabaseConnection
from auth.session import UserSession


class CategoryDAO:
    """Category data access with hierarchy, status, and safe archive semantics."""

    def __init__(self):
        self.db = DatabaseConnection()

    def _uid(self):
        uid = UserSession.get_current_user_id()
        if not uid:
            raise Exception("لا توجد جلسة مستخدم فعالة")
        return uid

    def _normalize_parent(self, parent_id):
        if parent_id in (None, '', 0, '0'):
            return None
        return int(parent_id)

    def get_by_id(self, cid: int) -> Optional[Dict]:
        if self.db.is_remote():
            for category in self.db.get_rest_client().get_categories(include_inactive=True, include_deleted=True):
                if int(category.get('id', 0)) == int(cid):
                    return category
            return None
        uid = self._uid()
        row = self.db.execute('''
            SELECT c.*, p.name AS parent_name,
                   (SELECT COUNT(*) FROM items i WHERE i.category_id = c.id AND i.user_id = c.user_id AND COALESCE(i.deleted_at, '') = '') AS item_count,
                   (SELECT COUNT(*) FROM categories ch WHERE ch.parent_id = c.id AND ch.user_id = c.user_id AND COALESCE(ch.deleted_at, '') = '') AS child_count
            FROM categories c
            LEFT JOIN categories p ON p.id = c.parent_id
            WHERE c.id = ? AND c.user_id = ?
        ''', (cid, uid)).fetchone()
        return dict(row) if row else None

    def get_all(self, search=None, include_inactive: bool = False, include_deleted: bool = False):
        if self.db.is_remote():
            return self.db.get_rest_client().get_categories(search=search, include_inactive=include_inactive, include_deleted=include_deleted)
        uid = UserSession.get_current_user_id()
        if not uid:
            return []
        query = '''
            SELECT c.*, p.name AS parent_name,
                   (SELECT COUNT(*) FROM items i WHERE i.category_id = c.id AND i.user_id = c.user_id AND COALESCE(i.deleted_at, '') = '') AS item_count,
                   (SELECT COUNT(*) FROM categories ch WHERE ch.parent_id = c.id AND ch.user_id = c.user_id AND COALESCE(ch.deleted_at, '') = '') AS child_count
            FROM categories c
            LEFT JOIN categories p ON p.id = c.parent_id
            WHERE c.user_id = ?
        '''
        params = [uid]
        if not include_deleted:
            query += " AND COALESCE(c.deleted_at, '') = ''"
        if not include_inactive:
            query += " AND COALESCE(c.is_active, 1) = 1"
        if search:
            query += " AND (c.name LIKE ? OR COALESCE(c.description, '') LIKE ? OR COALESCE(p.name, '') LIKE ?)"
            like = f"%{search}%"
            params.extend([like, like, like])
        query += " ORDER BY COALESCE(p.name, ''), c.name"
        rows = self.db.execute(query, params).fetchall()
        cats = [dict(row) for row in rows]
        by_id = {c['id']: c for c in cats}
        for c in cats:
            names = [c.get('name') or '']
            parent_id = c.get('parent_id')
            guard = set()
            while parent_id and parent_id in by_id and parent_id not in guard:
                guard.add(parent_id)
                parent = by_id[parent_id]
                names.insert(0, parent.get('name') or '')
                parent_id = parent.get('parent_id')
            c['full_name'] = ' / '.join([x for x in names if x])
            c['status_text'] = 'نشط' if int(c.get('is_active') or 0) == 1 and not c.get('deleted_at') else 'مؤرشف'
        return cats

    def _validate(self, name: str, parent_id=None, category_id: int | None = None):
        uid = self._uid()
        name = (name or '').strip()
        if not name:
            raise Exception("اسم التصنيف مطلوب")
        parent_id = self._normalize_parent(parent_id)
        if category_id and parent_id == int(category_id):
            raise Exception("لا يمكن أن يكون التصنيف أباً لنفسه")
        if parent_id:
            parent = self.get_by_id(parent_id)
            if not parent or parent.get('deleted_at'):
                raise Exception("التصنيف الأب غير موجود أو مؤرشف")
            current = parent.get('parent_id')
            guard = set()
            while current and current not in guard:
                if category_id and int(current) == int(category_id):
                    raise Exception("لا يمكن إنشاء حلقة في شجرة التصنيفات")
                guard.add(current)
                p = self.get_by_id(current)
                current = p.get('parent_id') if p else None
        dup = self.db.execute('''
            SELECT id FROM categories
            WHERE user_id = ? AND name = ? AND COALESCE(parent_id, 0) = COALESCE(?, 0)
              AND COALESCE(deleted_at, '') = ''
              AND (? IS NULL OR id <> ?)
        ''', (uid, name, parent_id, category_id, category_id)).fetchone()
        if dup:
            raise Exception("يوجد تصنيف بنفس الاسم ضمن نفس المستوى")
        return name, parent_id

    def add(self, name, parent_id=None, description='', color='#64748B', icon='folder', is_active=1):
        if self.db.is_remote():
            return self.db.get_rest_client().add_category({
                'name': name, 'parent_id': parent_id, 'description': description,
                'color': color, 'icon': icon, 'is_active': is_active
            })
        uid = self._uid()
        name, parent_id = self._validate(name, parent_id)
        cur = self.db.execute('''
            INSERT INTO categories (user_id, name, parent_id, description, color, icon, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (uid, name, parent_id, description or '', color or '#64748B', icon or 'folder', 1 if is_active else 0))
        self.db.commit()
        return cur.lastrowid

    def update(self, cid, data_or_name, parent_id=None, description=None, color=None, icon=None, is_active=None):
        if self.db.is_remote():
            if isinstance(data_or_name, dict):
                data = dict(data_or_name)
            else:
                data = {'name': data_or_name, 'parent_id': parent_id, 'description': description or '', 'color': color or '#64748B', 'icon': icon or 'folder', 'is_active': 1 if is_active is None else is_active}
            self.db.get_rest_client().update_category(int(cid), data)
            return
        uid = self._uid()
        if isinstance(data_or_name, dict):
            data = dict(data_or_name)
            name = data.get('name')
            parent_id = data.get('parent_id')
            description = data.get('description', '')
            color = data.get('color', '#64748B')
            icon = data.get('icon', 'folder')
            is_active = data.get('is_active', 1)
        else:
            name = data_or_name
        name, parent_id = self._validate(name, parent_id, int(cid))
        self.db.execute('''
            UPDATE categories
            SET name = ?, parent_id = ?, description = ?, color = ?, icon = ?, is_active = ?
            WHERE id = ? AND user_id = ?
        ''', (name, parent_id, description or '', color or '#64748B', icon or 'folder', 1 if is_active else 0, cid, uid))
        self.db.commit()

    def archive(self, cid):
        if self.db.is_remote():
            self.db.get_rest_client().delete_category(int(cid))
            return
        uid = self._uid()
        now = datetime.datetime.now().isoformat()
        self.db.execute("UPDATE categories SET deleted_at = ?, is_active = 0 WHERE id = ? AND user_id = ?", (now, cid, uid))
        self.db.commit()

    def restore(self, cid):
        if self.db.is_remote():
            self.db.get_rest_client().restore_category(int(cid))
            return
        uid = self._uid()
        self.db.execute("UPDATE categories SET deleted_at = NULL, is_active = 1 WHERE id = ? AND user_id = ?", (cid, uid))
        self.db.commit()

    def delete(self, cid):
        if self.db.is_remote():
            self.db.get_rest_client().delete_category(int(cid))
            return
        uid = self._uid()
        cur = self.db.execute("SELECT id FROM items WHERE category_id=? AND user_id=? AND COALESCE(deleted_at, '') = '' LIMIT 1", (cid, uid))
        if cur.fetchone():
            raise Exception("لا يمكن حذف التصنيف لوجود مواد مرتبطة به. انقل المواد أولاً أو أرشف التصنيف فقط.")
        child = self.db.execute("SELECT id FROM categories WHERE parent_id=? AND user_id=? AND COALESCE(deleted_at, '') = '' LIMIT 1", (cid, uid)).fetchone()
        if child:
            raise Exception("لا يمكن حذف التصنيف لوجود تصنيفات فرعية. انقلها أو أرشفها أولاً.")
        self.archive(cid)


category_dao = CategoryDAO()
