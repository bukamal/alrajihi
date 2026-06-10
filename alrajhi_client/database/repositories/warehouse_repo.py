# -*- coding: utf-8 -*-
from __future__ import annotations

import datetime
from decimal import Decimal
from typing import Dict, List, Optional

from database.repositories.base_repo import BaseRepository
from auth.session import UserSession

DEFAULT_WAREHOUSE_NAME = 'المستودع الرئيسي'


class WarehouseRepository(BaseRepository):
    """Warehouse-1 local repository: master data + read-only balances."""

    def _now(self) -> str:
        return datetime.datetime.now().isoformat()

    def _uid(self) -> str:
        return UserSession.get_current_user_id() or 'admin'

    def ensure_schema(self) -> None:
        if self.db.is_remote():
            return
        conn = self.db.get_connection()
        conn.execute('PRAGMA foreign_keys=ON')
        conn.executescript('''
            CREATE TABLE IF NOT EXISTS warehouses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                name TEXT NOT NULL,
                code TEXT,
                location TEXT,
                notes TEXT,
                is_default INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                deleted_at TEXT,
                created_at TEXT,
                updated_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id),
                UNIQUE(user_id, name)
            );
            CREATE TABLE IF NOT EXISTS item_warehouse_balances (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                item_id INTEGER NOT NULL,
                warehouse_id INTEGER NOT NULL,
                quantity TEXT DEFAULT '0',
                average_cost TEXT DEFAULT '0',
                updated_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (item_id) REFERENCES items(id),
                FOREIGN KEY (warehouse_id) REFERENCES warehouses(id),
                UNIQUE(user_id, item_id, warehouse_id)
            );
            CREATE TABLE IF NOT EXISTS warehouse_movements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                item_id INTEGER NOT NULL,
                warehouse_id INTEGER NOT NULL,
                movement_type TEXT NOT NULL,
                quantity TEXT NOT NULL,
                unit_cost TEXT,
                reference_type TEXT,
                reference_id INTEGER,
                notes TEXT,
                movement_date TEXT,
                created_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (item_id) REFERENCES items(id),
                FOREIGN KEY (warehouse_id) REFERENCES warehouses(id)
            );
            CREATE INDEX IF NOT EXISTS idx_wh_user ON warehouses(user_id);
            CREATE INDEX IF NOT EXISTS idx_wh_bal_item ON item_warehouse_balances(item_id);
            CREATE INDEX IF NOT EXISTS idx_wh_bal_wh ON item_warehouse_balances(warehouse_id);
            CREATE INDEX IF NOT EXISTS idx_wh_mov_item ON warehouse_movements(item_id);
            CREATE INDEX IF NOT EXISTS idx_wh_mov_wh ON warehouse_movements(warehouse_id);
        ''')
        conn.commit()

    def bootstrap_defaults(self) -> None:
        if self.db.is_remote():
            return
        self.ensure_schema()
        conn = self.db.get_connection()
        now = self._now()
        users = conn.execute('''
            SELECT id FROM users
            UNION
            SELECT DISTINCT user_id AS id FROM items WHERE user_id IS NOT NULL
        ''').fetchall()
        for user in users:
            uid = user['id']
            row = conn.execute(
                "SELECT id FROM warehouses WHERE user_id=? AND is_default=1 AND deleted_at IS NULL LIMIT 1",
                (uid,)
            ).fetchone()
            if row:
                wh_id = row['id']
            else:
                cur = conn.execute('''
                    INSERT OR IGNORE INTO warehouses
                    (user_id, name, code, location, notes, is_default, is_active, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, 1, 1, ?, ?)
                ''', (uid, DEFAULT_WAREHOUSE_NAME, 'MAIN', '', 'تم إنشاؤه تلقائياً عند تفعيل نظام المستودعات', now, now))
                wh_id = cur.lastrowid or conn.execute(
                    "SELECT id FROM warehouses WHERE user_id=? AND name=? LIMIT 1",
                    (uid, DEFAULT_WAREHOUSE_NAME)
                ).fetchone()['id']
            for item in conn.execute('''
                SELECT id, COALESCE(quantity, '0') AS quantity, COALESCE(average_cost, '0') AS average_cost
                FROM items WHERE user_id=? AND deleted_at IS NULL
            ''', (uid,)).fetchall():
                if conn.execute('''
                    SELECT id FROM item_warehouse_balances
                    WHERE user_id=? AND item_id=? AND warehouse_id=?
                ''', (uid, item['id'], wh_id)).fetchone():
                    continue
                qty = str(item['quantity'] or '0')
                avg = str(item['average_cost'] or '0')
                conn.execute('''
                    INSERT INTO item_warehouse_balances
                    (user_id, item_id, warehouse_id, quantity, average_cost, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (uid, item['id'], wh_id, qty, avg, now))
                try:
                    nonzero = Decimal(qty) != 0
                except Exception:
                    nonzero = False
                if nonzero:
                    conn.execute('''
                        INSERT INTO warehouse_movements
                        (user_id, item_id, warehouse_id, movement_type, quantity, unit_cost, reference_type, notes, movement_date, created_at)
                        VALUES (?, ?, ?, 'migration_opening', ?, ?, 'migration', ?, ?, ?)
                    ''', (uid, item['id'], wh_id, qty, avg, 'ترحيل رصيد المادة إلى المستودع الرئيسي', now, now))
        conn.commit()

    def default_warehouse_id(self, user_id: str | None = None) -> Optional[int]:
        if self.db.is_remote():
            return None
        self.bootstrap_defaults()
        uid = user_id or self._uid()
        row = self.db.get_connection().execute(
            "SELECT id FROM warehouses WHERE user_id=? AND is_default=1 AND deleted_at IS NULL LIMIT 1", (uid,)
        ).fetchone()
        return int(row['id']) if row else None

    def list_warehouses(self, include_archived: bool = False) -> List[Dict]:
        if self.db.is_remote():
            return []
        self.bootstrap_defaults()
        uid = self._uid()
        sql = '''
            SELECT w.*, COUNT(DISTINCT b.item_id) AS item_count,
                   COALESCE(SUM(CAST(b.quantity AS REAL)), 0) AS total_qty
            FROM warehouses w
            LEFT JOIN item_warehouse_balances b ON b.warehouse_id = w.id
            WHERE w.user_id=?
        '''
        params = [uid]
        if not include_archived:
            sql += " AND w.deleted_at IS NULL AND COALESCE(w.is_active, 1)=1"
        sql += " GROUP BY w.id ORDER BY w.is_default DESC, w.name"
        return [dict(r) for r in self.db.get_connection().execute(sql, params).fetchall()]

    def get_by_id(self, warehouse_id: int) -> Optional[Dict]:
        if self.db.is_remote():
            return None
        self.bootstrap_defaults()
        uid = self._uid()
        row = self.db.get_connection().execute("SELECT * FROM warehouses WHERE id=? AND user_id=?", (warehouse_id, uid)).fetchone()
        return dict(row) if row else None

    def add(self, data: Dict) -> int:
        if self.db.is_remote():
            raise NotImplementedError('Warehouses REST API will be introduced in a later stage')
        self.bootstrap_defaults()
        uid = self._uid()
        now = self._now()
        conn = self.db.get_connection()
        cur = conn.execute('''
            INSERT INTO warehouses (user_id, name, code, location, notes, is_default, is_active, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, 0, 1, ?, ?)
        ''', (uid, data['name'].strip(), data.get('code', '').strip(), data.get('location', '').strip(), data.get('notes', '').strip(), now, now))
        conn.commit()
        return int(cur.lastrowid)

    def update(self, warehouse_id: int, data: Dict) -> None:
        if self.db.is_remote():
            raise NotImplementedError('Warehouses REST API will be introduced in a later stage')
        self.bootstrap_defaults()
        uid = self._uid()
        conn = self.db.get_connection()
        row = conn.execute("SELECT id FROM warehouses WHERE id=? AND user_id=?", (warehouse_id, uid)).fetchone()
        if not row:
            raise ValueError('المستودع غير موجود')
        conn.execute('''
            UPDATE warehouses SET name=?, code=?, location=?, notes=?, is_active=?, updated_at=?
            WHERE id=? AND user_id=?
        ''', (data['name'].strip(), data.get('code', '').strip(), data.get('location', '').strip(), data.get('notes', '').strip(), 1 if data.get('is_active', 1) else 0, self._now(), warehouse_id, uid))
        conn.commit()

    def archive(self, warehouse_id: int) -> None:
        if self.db.is_remote():
            raise NotImplementedError('Warehouses REST API will be introduced in a later stage')
        self.bootstrap_defaults()
        uid = self._uid()
        conn = self.db.get_connection()
        wh = conn.execute("SELECT is_default FROM warehouses WHERE id=? AND user_id=?", (warehouse_id, uid)).fetchone()
        if not wh:
            raise ValueError('المستودع غير موجود')
        if int(wh['is_default'] or 0) == 1:
            raise ValueError('لا يمكن أرشفة المستودع الرئيسي')
        bal = conn.execute('''
            SELECT COUNT(*) AS c FROM item_warehouse_balances
            WHERE warehouse_id=? AND ABS(CAST(quantity AS REAL)) > 0.000001
        ''', (warehouse_id,)).fetchone()
        if bal and int(bal['c']) > 0:
            raise ValueError('لا يمكن أرشفة مستودع يحتوي أرصدة مواد. انقل الرصيد أولاً في مرحلة التحويلات.')
        now = self._now()
        conn.execute("UPDATE warehouses SET deleted_at=?, is_active=0, updated_at=? WHERE id=? AND user_id=?", (now, now, warehouse_id, uid))
        conn.commit()

    def balances(self, search: str | None = None, warehouse_id: int | None = None, limit: int | None = None, offset: int | None = None) -> List[Dict]:
        if self.db.is_remote():
            return []
        self.bootstrap_defaults()
        uid = self._uid()
        sql = '''
            SELECT b.id, b.item_id, i.name AS item_name, i.barcode, i.unit,
                   b.warehouse_id, w.name AS warehouse_name, b.quantity, b.average_cost,
                   (CAST(COALESCE(b.quantity, '0') AS REAL) * CAST(COALESCE(b.average_cost, '0') AS REAL)) AS stock_value,
                   b.updated_at
            FROM item_warehouse_balances b
            JOIN items i ON i.id = b.item_id
            JOIN warehouses w ON w.id = b.warehouse_id
            WHERE b.user_id=? AND i.deleted_at IS NULL AND w.deleted_at IS NULL
        '''
        params = [uid]
        if search:
            sql += " AND (i.name LIKE ? OR i.barcode LIKE ? OR w.name LIKE ?)"
            s = f'%{search}%'
            params.extend([s, s, s])
        if warehouse_id:
            sql += " AND b.warehouse_id=?"
            params.append(warehouse_id)
        sql += " ORDER BY w.is_default DESC, w.name, i.name"
        if limit is not None:
            sql += " LIMIT ?"
            params.append(limit)
        if offset is not None:
            sql += " OFFSET ?"
            params.append(offset)
        return [dict(r) for r in self.db.get_connection().execute(sql, params).fetchall()]

    def balance_count(self, search: str | None = None, warehouse_id: int | None = None) -> int:
        if self.db.is_remote():
            return 0
        return len(self.balances(search=search, warehouse_id=warehouse_id))

    def movements(self, item_id: int | None = None, warehouse_id: int | None = None, limit: int = 100) -> List[Dict]:
        if self.db.is_remote():
            return []
        self.bootstrap_defaults()
        uid = self._uid()
        sql = '''
            SELECT m.*, i.name AS item_name, w.name AS warehouse_name
            FROM warehouse_movements m
            JOIN items i ON i.id = m.item_id
            JOIN warehouses w ON w.id = m.warehouse_id
            WHERE m.user_id=?
        '''
        params = [uid]
        if item_id:
            sql += ' AND m.item_id=?'
            params.append(item_id)
        if warehouse_id:
            sql += ' AND m.warehouse_id=?'
            params.append(warehouse_id)
        sql += ' ORDER BY m.id DESC LIMIT ?'
        params.append(limit)
        return [dict(r) for r in self.db.get_connection().execute(sql, params).fetchall()]
