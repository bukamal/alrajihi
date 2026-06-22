# -*- coding: utf-8 -*-
from __future__ import annotations

import datetime
from decimal import Decimal
from typing import Dict, List, Optional

from database.repositories.base_repo import BaseRepository
from auth.session import UserSession
from database.repositories.branch_repo import BranchRepository

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
                branch_id INTEGER,
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
            CREATE TABLE IF NOT EXISTS item_warehouse_variant_balances (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                item_id INTEGER NOT NULL,
                variant_id INTEGER NOT NULL,
                warehouse_id INTEGER NOT NULL,
                variant_color TEXT,
                variant_size TEXT,
                variant_sku TEXT,
                quantity TEXT DEFAULT '0',
                average_cost TEXT DEFAULT '0',
                updated_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (item_id) REFERENCES items(id),
                FOREIGN KEY (variant_id) REFERENCES item_variants(id),
                FOREIGN KEY (warehouse_id) REFERENCES warehouses(id),
                UNIQUE(user_id, item_id, variant_id, warehouse_id)
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
                variant_id INTEGER,
                variant_color TEXT,
                variant_size TEXT,
                variant_sku TEXT,
                barcode_scope TEXT,
                matched_barcode TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (item_id) REFERENCES items(id),
                FOREIGN KEY (warehouse_id) REFERENCES warehouses(id)
            );

            CREATE TABLE IF NOT EXISTS warehouse_transfers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                transfer_no TEXT NOT NULL,
                item_id INTEGER NOT NULL,
                from_warehouse_id INTEGER NOT NULL,
                to_warehouse_id INTEGER NOT NULL,
                quantity TEXT NOT NULL,
                base_qty TEXT,
                unit_id INTEGER,
                unit_name TEXT,
                conversion_factor TEXT DEFAULT '1',
                barcode_scope TEXT,
                matched_barcode TEXT,
                variant_id INTEGER,
                variant_color TEXT,
                variant_size TEXT,
                variant_sku TEXT,
                unit_cost TEXT DEFAULT '0',
                notes TEXT,
                status TEXT DEFAULT 'active',
                created_at TEXT,
                cancelled_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (item_id) REFERENCES items(id),
                FOREIGN KEY (from_warehouse_id) REFERENCES warehouses(id),
                FOREIGN KEY (to_warehouse_id) REFERENCES warehouses(id),
                UNIQUE(user_id, transfer_no)
            );
            CREATE INDEX IF NOT EXISTS idx_wh_user ON warehouses(user_id);
            CREATE INDEX IF NOT EXISTS idx_wh_bal_item ON item_warehouse_balances(item_id);
            CREATE INDEX IF NOT EXISTS idx_wh_bal_wh ON item_warehouse_balances(warehouse_id);
            CREATE INDEX IF NOT EXISTS idx_wh_variant_balances_variant ON item_warehouse_variant_balances(variant_id);
            CREATE INDEX IF NOT EXISTS idx_wh_variant_balances_wh ON item_warehouse_variant_balances(warehouse_id);
            CREATE INDEX IF NOT EXISTS idx_wh_mov_item ON warehouse_movements(item_id);
            CREATE INDEX IF NOT EXISTS idx_wh_mov_wh ON warehouse_movements(warehouse_id);
        ''')
        try:
            conn.execute("ALTER TABLE warehouses ADD COLUMN branch_id INTEGER")
        except Exception:
            pass
        for col_name, col_type in (
            ('base_qty', 'TEXT'), ('unit_id', 'INTEGER'), ('unit_name', 'TEXT'),
            ('conversion_factor', "TEXT DEFAULT '1'"), ('barcode_scope', 'TEXT'), ('matched_barcode', 'TEXT'),
            ('variant_id', 'INTEGER'), ('variant_color', 'TEXT'), ('variant_size', 'TEXT'), ('variant_sku', 'TEXT'),
        ):
            try:
                conn.execute(f"ALTER TABLE warehouse_transfers ADD COLUMN {col_name} {col_type}")
            except Exception:
                pass
        for col_name, col_type in (
            ('variant_id', 'INTEGER'), ('variant_color', 'TEXT'), ('variant_size', 'TEXT'),
            ('variant_sku', 'TEXT'), ('barcode_scope', 'TEXT'), ('matched_barcode', 'TEXT'),
        ):
            try:
                conn.execute(f"ALTER TABLE warehouse_movements ADD COLUMN {col_name} {col_type}")
            except Exception:
                pass
        try:
            conn.execute("CREATE INDEX IF NOT EXISTS idx_wh_transfer_unit ON warehouse_transfers(unit_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_wh_mov_variant ON warehouse_movements(variant_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_wh_variant_balances_variant ON item_warehouse_variant_balances(variant_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_wh_variant_balances_wh ON item_warehouse_variant_balances(warehouse_id)")
        except Exception:
            pass
        conn.commit()

    def bootstrap_defaults(self) -> None:
        if self.db.is_remote():
            return
        self.ensure_schema()
        try:
            BranchRepository().bootstrap_defaults()
        except Exception:
            pass
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
                try:
                    default_branch_id = BranchRepository().default_branch_id(uid)
                except Exception:
                    default_branch_id = None
                cur = conn.execute('''
                    INSERT OR IGNORE INTO warehouses
                    (user_id, name, code, location, notes, branch_id, is_default, is_active, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, 1, 1, ?, ?)
                ''', (uid, DEFAULT_WAREHOUSE_NAME, 'MAIN', '', 'تم إنشاؤه تلقائياً عند تفعيل نظام المستودعات', default_branch_id, now, now))
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
                movement_count = conn.execute("SELECT COUNT(*) AS cnt FROM inventory_movements WHERE item_id=? AND user_id=?", (item['id'], uid)).fetchone()['cnt']
                non_opening_count = conn.execute("SELECT COUNT(*) AS cnt FROM inventory_movements WHERE item_id=? AND user_id=? AND movement_type <> 'opening'", (item['id'], uid)).fetchone()['cnt']
                opening_row = conn.execute("SELECT COALESCE(SUM(CAST(quantity AS REAL)), 0) AS qty FROM inventory_movements WHERE item_id=? AND user_id=? AND movement_type='opening'", (item['id'], uid)).fetchone()
                # If only an opening movement exists, seed the warehouse with that
                # opening quantity.  If transactional movements already exist, do not
                # migrate item.quantity because invoice/return/production movements are
                # already reflected in warehouse rows or will be reconciled separately.
                if movement_count and not non_opening_count:
                    qty = str(opening_row['qty'] if opening_row else item['quantity'] or '0')
                elif movement_count:
                    qty = '0'
                else:
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
            return self.db.get_rest_client().default_warehouse_id()
        self.bootstrap_defaults()
        uid = user_id or self._uid()
        row = self.db.get_connection().execute(
            "SELECT id FROM warehouses WHERE user_id=? AND is_default=1 AND deleted_at IS NULL LIMIT 1", (uid,)
        ).fetchone()
        return int(row['id']) if row else None

    def list_warehouses(self, include_archived: bool = False) -> List[Dict]:
        if self.db.is_remote():
            return self.db.get_rest_client().get_warehouses(include_archived)
        self.bootstrap_defaults()
        uid = self._uid()
        sql = '''
            SELECT w.*, br.name AS branch_name, COUNT(DISTINCT b.item_id) AS item_count,
                   COALESCE(SUM(CAST(b.quantity AS REAL)), 0) AS total_qty
            FROM warehouses w
            LEFT JOIN branches br ON br.id = w.branch_id
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
            return self.db.get_rest_client().get_warehouse(warehouse_id)
        self.bootstrap_defaults()
        uid = self._uid()
        row = self.db.get_connection().execute("SELECT * FROM warehouses WHERE id=? AND user_id=?", (warehouse_id, uid)).fetchone()
        return dict(row) if row else None

    def add(self, data: Dict) -> int:
        if self.db.is_remote():
            return self.db.get_rest_client().add_warehouse(data)
        self.bootstrap_defaults()
        uid = self._uid()
        now = self._now()
        conn = self.db.get_connection()
        cur = conn.execute('''
            INSERT INTO warehouses (user_id, name, code, location, notes, branch_id, is_default, is_active, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, 0, 1, ?, ?)
        ''', (uid, data['name'].strip(), data.get('code', '').strip(), data.get('location', '').strip(), data.get('notes', '').strip(), data.get('branch_id') or BranchRepository().default_branch_id(uid), now, now))
        conn.commit()
        return int(cur.lastrowid)

    def update(self, warehouse_id: int, data: Dict) -> None:
        if self.db.is_remote():
            return self.db.get_rest_client().update_warehouse(warehouse_id, data)
        self.bootstrap_defaults()
        uid = self._uid()
        conn = self.db.get_connection()
        row = conn.execute("SELECT id FROM warehouses WHERE id=? AND user_id=?", (warehouse_id, uid)).fetchone()
        if not row:
            raise ValueError('المستودع غير موجود')
        conn.execute('''
            UPDATE warehouses SET name=?, code=?, location=?, notes=?, branch_id=?, is_active=?, updated_at=?
            WHERE id=? AND user_id=?
        ''', (data['name'].strip(), data.get('code', '').strip(), data.get('location', '').strip(), data.get('notes', '').strip(), data.get('branch_id') or BranchRepository().default_branch_id(uid), 1 if data.get('is_active', 1) else 0, self._now(), warehouse_id, uid))
        conn.commit()

    def archive(self, warehouse_id: int) -> None:
        if self.db.is_remote():
            return self.db.get_rest_client().archive_warehouse(warehouse_id)
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
            return self.db.get_rest_client().get_warehouse_balances(search=search, warehouse_id=warehouse_id, limit=limit, offset=offset)
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
            return self.db.get_rest_client().get_warehouse_balance_count(search=search, warehouse_id=warehouse_id)
        return len(self.balances(search=search, warehouse_id=warehouse_id))

    def movements(self, item_id: int | None = None, warehouse_id: int | None = None, limit: int = 100) -> List[Dict]:
        if self.db.is_remote():
            return self.db.get_rest_client().get_warehouse_movements(item_id=item_id, warehouse_id=warehouse_id, limit=limit)
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

    def default_warehouse(self) -> Optional[Dict]:
        wh_id = self.default_warehouse_id()
        return self.get_by_id(wh_id) if wh_id else None

    def available_qty(self, item_id: int, warehouse_id: int | None = None, variant_id: int | None = None) -> Decimal:
        if self.db.is_remote():
            return Decimal(str(self.db.get_rest_client().warehouse_available_qty(item_id, warehouse_id, variant_id=variant_id)))
        self.bootstrap_defaults()
        uid = self._uid()
        wh_id = warehouse_id or self.default_warehouse_id(uid)
        if not wh_id:
            return Decimal('0')
        if variant_id:
            return self._available_variant_qty(int(item_id), int(variant_id), int(wh_id))
        row = self.db.get_connection().execute("""
            SELECT quantity FROM item_warehouse_balances
            WHERE user_id=? AND item_id=? AND warehouse_id=?
        """, (uid, item_id, wh_id)).fetchone()
        return Decimal(str(row['quantity'])) if row and row['quantity'] is not None else Decimal('0')
    def _warehouse_active(self, warehouse_id: int) -> bool:
        uid = self._uid()
        row = self.db.get_connection().execute("""
            SELECT id FROM warehouses
            WHERE id=? AND user_id=? AND deleted_at IS NULL AND COALESCE(is_active, 1)=1
        """, (warehouse_id, uid)).fetchone()
        return bool(row)

    def _item_cost(self, item_id: int) -> Decimal:
        row = self.db.get_connection().execute(
            "SELECT COALESCE(average_cost, '0') AS average_cost FROM items WHERE id=?",
            (item_id,)
        ).fetchone()
        return Decimal(str(row['average_cost'])) if row else Decimal('0')

    def _ensure_balance_row(self, item_id: int, warehouse_id: int, unit_cost='0') -> None:
        uid = self._uid()
        now = self._now()
        conn = self.db.get_connection()
        if conn.execute("""
            SELECT id FROM item_warehouse_balances WHERE user_id=? AND item_id=? AND warehouse_id=?
        """, (uid, item_id, warehouse_id)).fetchone():
            return
        conn.execute("""
            INSERT INTO item_warehouse_balances
            (user_id, item_id, warehouse_id, quantity, average_cost, updated_at)
            VALUES (?, ?, ?, '0', ?, ?)
        """, (uid, item_id, warehouse_id, str(unit_cost or '0'), now))

    def _variant_payload(self, data: Dict | None = None) -> Dict:
        data = data or {}
        variant_id = data.get('variant_id')
        try:
            variant_id = int(variant_id) if variant_id not in (None, '', 0, '0') else None
        except Exception:
            variant_id = None
        return {
            'variant_id': variant_id,
            'variant_color': str(data.get('variant_color') or ''),
            'variant_size': str(data.get('variant_size') or ''),
            'variant_sku': str(data.get('variant_sku') or ''),
            'barcode_scope': str(data.get('barcode_scope') or ('variant' if variant_id else '')),
            'matched_barcode': str(data.get('matched_barcode') or data.get('barcode') or ''),
        }

    def _ensure_variant_balance_row(self, item_id: int, variant_id: int, warehouse_id: int, unit_cost='0', variant_payload: Dict | None = None) -> None:
        uid = self._uid()
        now = self._now()
        vp = self._variant_payload(variant_payload)
        conn = self.db.get_connection()
        if conn.execute("""
            SELECT id FROM item_warehouse_variant_balances
            WHERE user_id=? AND item_id=? AND variant_id=? AND warehouse_id=?
        """, (uid, item_id, variant_id, warehouse_id)).fetchone():
            return
        conn.execute("""
            INSERT INTO item_warehouse_variant_balances
            (user_id, item_id, variant_id, warehouse_id, variant_color, variant_size, variant_sku, quantity, average_cost, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, '0', ?, ?)
        """, (uid, item_id, variant_id, warehouse_id, vp['variant_color'], vp['variant_size'], vp['variant_sku'], str(unit_cost or '0'), now))

    def _available_variant_qty(self, item_id: int, variant_id: int, warehouse_id: int) -> Decimal:
        uid = self._uid()
        row = self.db.get_connection().execute("""
            SELECT quantity FROM item_warehouse_variant_balances
            WHERE user_id=? AND item_id=? AND variant_id=? AND warehouse_id=?
        """, (uid, item_id, variant_id, warehouse_id)).fetchone()
        return Decimal(str(row['quantity'])) if row and row['quantity'] is not None else Decimal('0')
    def record_movement(self, item_id, warehouse_id, movement_type, quantity, unit_cost='0', reference_type=None, reference_id=None, notes='', **variant_data) -> int:
        if self.db.is_remote():
            payload = {
                'item_id': item_id,
                'warehouse_id': warehouse_id,
                'movement_type': movement_type,
                'quantity': str(quantity or 0),
                'unit_cost': str(unit_cost or 0),
                'reference_type': reference_type,
                'reference_id': reference_id,
                'notes': notes or '',
            }
            payload.update(self._variant_payload(variant_data))
            return self.db.get_rest_client().warehouse_record_movement(payload)
        self.bootstrap_defaults()
        uid = self._uid()
        qty = Decimal(str(quantity or 0))
        cost = Decimal(str(unit_cost or 0))
        if qty == 0:
            return 0
        if not self._warehouse_active(int(warehouse_id)):
            raise ValueError('المستودع غير نشط أو غير موجود')
        vp = self._variant_payload(variant_data)
        conn = self.db.get_connection()
        now = self._now()
        self._ensure_balance_row(int(item_id), int(warehouse_id), cost)
        current = self.available_qty(int(item_id), int(warehouse_id))
        new_qty = current + qty
        if new_qty < 0:
            raise ValueError('الرصيد غير كافٍ في المستودع المحدد')
        avg_cost = str(cost if cost > 0 else self._item_cost(item_id))
        conn.execute("""
            UPDATE item_warehouse_balances SET quantity=?, average_cost=?, updated_at=?
            WHERE user_id=? AND item_id=? AND warehouse_id=?
        """, (str(new_qty), avg_cost, now, uid, int(item_id), int(warehouse_id)))
        if vp['variant_id']:
            self._ensure_variant_balance_row(int(item_id), int(vp['variant_id']), int(warehouse_id), cost, vp)
            current_variant = self._available_variant_qty(int(item_id), int(vp['variant_id']), int(warehouse_id))
            new_variant_qty = current_variant + qty
            if new_variant_qty < 0:
                raise ValueError('الرصيد غير كافٍ لهذا اللون/المقاس في المستودع المحدد')
            conn.execute("""
                UPDATE item_warehouse_variant_balances
                SET quantity=?, average_cost=?, variant_color=?, variant_size=?, variant_sku=?, updated_at=?
                WHERE user_id=? AND item_id=? AND variant_id=? AND warehouse_id=?
            """, (str(new_variant_qty), avg_cost, vp['variant_color'], vp['variant_size'], vp['variant_sku'], now, uid, int(item_id), int(vp['variant_id']), int(warehouse_id)))
        cur = conn.execute("""
            INSERT INTO warehouse_movements
            (user_id, item_id, warehouse_id, movement_type, quantity, unit_cost, reference_type, reference_id, notes, movement_date, created_at,
             variant_id, variant_color, variant_size, variant_sku, barcode_scope, matched_barcode)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (uid, int(item_id), int(warehouse_id), movement_type, str(qty), str(cost), reference_type, reference_id, notes or '', now, now,
              vp['variant_id'], vp['variant_color'], vp['variant_size'], vp['variant_sku'], vp['barcode_scope'], vp['matched_barcode']))
        conn.commit()
        return int(cur.lastrowid)
    def reverse_reference(self, reference_type, reference_id) -> None:
        if self.db.is_remote():
            return self.db.get_rest_client().warehouse_reverse_reference(reference_type, reference_id)
        self.bootstrap_defaults()
        uid = self._uid()
        conn = self.db.get_connection()
        # Reverse only the current net effect for a reference.  Older code
        # reversed every original movement even if a prior update had already
        # posted reverse_* rows, which over-reversed invoices edited before
        # deletion.  We aggregate originals and their reversals by base movement
        # type/item/warehouse/unit_cost and post a reversal only for non-zero net.
        rows = conn.execute("""
            SELECT * FROM warehouse_movements
            WHERE user_id=? AND reference_id=? AND reference_type IN (?, ?)
            ORDER BY id ASC
        """, (uid, reference_id, reference_type, 'reverse_' + str(reference_type))).fetchall()
        nets = {}
        variant_payloads = {}
        for r in rows:
            mt = str(r['movement_type'] or '')
            base_mt = mt[8:] if mt.startswith('reverse_') else mt
            vp = self._variant_payload(dict(r))
            # Phase 322: reverse-reference aggregation must include the apparel
            # variant identity.  Otherwise two sizes/colors of the same item may
            # collapse into one generic item reversal and corrupt variant stock.
            key = (
                r['item_id'],
                r['warehouse_id'],
                base_mt,
                str(r['unit_cost'] or '0'),
                vp['variant_id'],
                vp['variant_color'],
                vp['variant_size'],
                vp['variant_sku'],
                vp['barcode_scope'],
                vp['matched_barcode'],
            )
            nets[key] = nets.get(key, Decimal('0')) + Decimal(str(r['quantity'] or 0))
            variant_payloads[key] = vp
        for key, net_qty in nets.items():
            if net_qty == 0:
                continue
            item_id, warehouse_id, base_mt, unit_cost, *_variant_key = key
            reverse_type = 'reverse_' + str(base_mt)
            self.record_movement(
                item_id,
                warehouse_id,
                reverse_type,
                -net_qty,
                unit_cost,
                'reverse_' + str(reference_type),
                reference_id,
                'عكس حركة مستودعية',
                **variant_payloads.get(key, {}),
            )

    def _next_transfer_no(self) -> str:
        uid = self._uid()
        today = datetime.datetime.now().strftime('%Y%m%d')
        row = self.db.get_connection().execute("""
            SELECT COUNT(*) AS c FROM warehouse_transfers WHERE user_id=? AND transfer_no LIKE ?
        """, (uid, f'TR-{today}-%')).fetchone()
        return f"TR-{today}-{int(row['c'] or 0) + 1:04d}"

    def create_transfer(self, data: Dict) -> int:
        if self.db.is_remote():
            return self.db.get_rest_client().create_warehouse_transfer(data)
        self.bootstrap_defaults()
        uid = self._uid()
        item_id = int(data.get('item_id') or 0)
        from_wh = int(data.get('from_warehouse_id') or 0)
        to_wh = int(data.get('to_warehouse_id') or 0)
        qty = Decimal(str(data.get('quantity') or 0))
        conv_factor = Decimal(str(data.get('conversion_factor') or 1))
        if conv_factor <= 0:
            conv_factor = Decimal('1')
        base_qty = Decimal(str(data.get('base_qty', qty * conv_factor) or 0))
        notes = str(data.get('notes') or '').strip()
        vp = self._variant_payload(data)
        if item_id <= 0:
            raise ValueError('اختر المادة')
        if from_wh <= 0 or to_wh <= 0:
            raise ValueError('اختر مستودع المصدر والوجهة')
        if from_wh == to_wh:
            raise ValueError('لا يمكن التحويل إلى نفس المستودع')
        if qty <= 0 or base_qty <= 0:
            raise ValueError('كمية التحويل يجب أن تكون أكبر من صفر')
        if not self._warehouse_active(from_wh) or not self._warehouse_active(to_wh):
            raise ValueError('لا يمكن التحويل من أو إلى مستودع مؤرشف')
        available = self.available_qty(item_id, from_wh, variant_id=vp['variant_id'])
        if available < base_qty:
            raise ValueError(f'الرصيد غير كافٍ في المستودع المصدر. المتاح: {available}')
        unit_cost = self._item_cost(item_id)
        conn = self.db.get_connection()
        transfer_no = self._next_transfer_no()
        now = self._now()
        cur = conn.execute("""
            INSERT INTO warehouse_transfers
            (user_id, transfer_no, item_id, from_warehouse_id, to_warehouse_id, quantity, base_qty, unit_id, unit_name, conversion_factor, barcode_scope, matched_barcode,
             variant_id, variant_color, variant_size, variant_sku, unit_cost, notes, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?)
        """, (uid, transfer_no, item_id, from_wh, to_wh, str(qty), str(base_qty), data.get('unit_id'), data.get('unit_name') or data.get('unit') or '', str(conv_factor), vp['barcode_scope'], vp['matched_barcode'], vp['variant_id'], vp['variant_color'], vp['variant_size'], vp['variant_sku'], str(unit_cost), notes, now))
        transfer_id = int(cur.lastrowid)
        conn.commit()
        self.record_movement(item_id, from_wh, 'transfer_out', -base_qty, unit_cost, 'warehouse_transfer', transfer_id, f'تحويل إلى مستودع #{to_wh}: {notes}', **vp)
        self.record_movement(item_id, to_wh, 'transfer_in', base_qty, unit_cost, 'warehouse_transfer', transfer_id, f'تحويل من مستودع #{from_wh}: {notes}', **vp)
        return transfer_id
    def cancel_transfer(self, transfer_id: int) -> None:
        if self.db.is_remote():
            return self.db.get_rest_client().cancel_warehouse_transfer(transfer_id)
        self.bootstrap_defaults()
        uid = self._uid()
        conn = self.db.get_connection()
        t = conn.execute("""
            SELECT * FROM warehouse_transfers WHERE id=? AND user_id=?
        """, (transfer_id, uid)).fetchone()
        if not t:
            raise ValueError('التحويل غير موجود')
        if t['status'] != 'active':
            raise ValueError('التحويل ملغى مسبقاً')
        qty = Decimal(str(t['base_qty'] if 'base_qty' in t.keys() and t['base_qty'] not in (None, '') else t['quantity'] or 0))
        vp = self._variant_payload(dict(t))
        if self.available_qty(t['item_id'], t['to_warehouse_id'], variant_id=vp['variant_id']) < qty:
            raise ValueError('لا يمكن إلغاء التحويل لأن رصيد المستودع المستلم غير كافٍ')
        unit_cost = Decimal(str(t['unit_cost'] or 0))
        self.record_movement(t['item_id'], t['to_warehouse_id'], 'transfer_cancel_out', -qty, unit_cost, 'warehouse_transfer_cancel', transfer_id, 'إلغاء تحويل مستودعي', **vp)
        self.record_movement(t['item_id'], t['from_warehouse_id'], 'transfer_cancel_in', qty, unit_cost, 'warehouse_transfer_cancel', transfer_id, 'إلغاء تحويل مستودعي', **vp)
        now = self._now()
        conn.execute("UPDATE warehouse_transfers SET status='cancelled', cancelled_at=? WHERE id=? AND user_id=?", (now, transfer_id, uid))
        conn.commit()
    def transfers(self, limit: int = 200) -> List[Dict]:
        if self.db.is_remote():
            return self.db.get_rest_client().get_warehouse_transfers(limit=limit)
        self.bootstrap_defaults()
        uid = self._uid()
        rows = self.db.get_connection().execute("""
            SELECT t.*, i.name AS item_name, fw.name AS from_warehouse_name, tw.name AS to_warehouse_name
            FROM warehouse_transfers t
            JOIN items i ON i.id = t.item_id
            JOIN warehouses fw ON fw.id = t.from_warehouse_id
            JOIN warehouses tw ON tw.id = t.to_warehouse_id
            WHERE t.user_id=?
            ORDER BY t.id DESC LIMIT ?
        """, (uid, limit)).fetchall()
        return [dict(r) for r in rows]

