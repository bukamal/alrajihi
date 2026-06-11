# -*- coding: utf-8 -*-
import sqlite3
import os
import json
import datetime
from typing import List, Dict, Optional, Tuple
from decimal import Decimal
from PyQt5.QtCore import QSettings

# ========== المسارات ==========
def get_local_db_path():
    if os.name == 'nt':
        appdata = os.environ.get('APPDATA', os.path.expanduser('~\\AppData\\Roaming'))
        data_dir = os.path.join(appdata, 'Alrajhi')
    else:
        data_dir = os.path.expanduser('~/.alrajhi')
    os.makedirs(data_dir, exist_ok=True)
    return os.path.join(data_dir, 'alrajhi_data.db')

LOCAL_DB_PATH = get_local_db_path()
OFFLINE_DB_PATH = os.path.join(os.path.dirname(LOCAL_DB_PATH), 'offline_queue.db')

# ========== Offline Queue Manager ==========
import hashlib
from auth.activation import get_device_id

def get_session_id():
    return hashlib.md5(get_device_id().encode()).hexdigest()

class OfflineQueueManager:
    def __init__(self):
        self._init_db()
    
    def _init_db(self):
        conn = sqlite3.connect(OFFLINE_DB_PATH)
        conn.execute('''
            CREATE TABLE IF NOT EXISTS queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                endpoint TEXT NOT NULL,
                method TEXT NOT NULL,
                data TEXT,
                created_at TEXT,
                record_id INTEGER,
                etag TEXT
            )
        ''')
        conn.commit()
        conn.close()
    
    def add_request(self, endpoint, method, data=None, record_id=None, etag=None):
        session_id = get_session_id()
        conn = sqlite3.connect(OFFLINE_DB_PATH)
        now = datetime.datetime.now().isoformat()
        conn.execute('''
            INSERT INTO queue (session_id, endpoint, method, data, created_at, record_id, etag)
            VALUES (?,?,?,?,?,?,?)
        ''', (session_id, endpoint, method, json.dumps(data) if data else None, now, record_id, etag))
        conn.commit()
        conn.close()
    
    def get_all_requests(self):
        session_id = get_session_id()
        conn = sqlite3.connect(OFFLINE_DB_PATH)
        conn.row_factory = sqlite3.Row
        rows = conn.execute('SELECT * FROM queue WHERE session_id = ? ORDER BY id', (session_id,)).fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def delete_request(self, req_id):
        conn = sqlite3.connect(OFFLINE_DB_PATH)
        conn.execute('DELETE FROM queue WHERE id=?', (req_id,))
        conn.commit()
        conn.close()

offline_queue = OfflineQueueManager()

# ========== DatabaseConnection ==========
class DatabaseConnection:
    _instance = None
    _local_conn = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_mode()
        return cls._instance

    def _init_mode(self):
        settings = QSettings("Alrajhi", "Accounting")
        self.mode = settings.value("network/mode", "local")
        self.server_url = settings.value("network/server_url", "http://localhost:8000")
        self._rest_client = None
        if self.mode == "client":
            from .connection_rest import RestClient
            self._rest_client = RestClient(self.server_url)

    def is_remote(self) -> bool:
        return self.mode == "client"

    def get_rest_client(self):
        return self._rest_client

    def set_token(self, token: str):
        if self._rest_client:
            self._rest_client.set_token(token)

    def get_connection(self):
        if self.mode != "client":
            if self._local_conn is None:
                os.makedirs(os.path.dirname(LOCAL_DB_PATH), exist_ok=True)
                self._local_conn = sqlite3.connect(LOCAL_DB_PATH, isolation_level=None)
                self._local_conn.row_factory = sqlite3.Row
                self._local_conn.execute('PRAGMA journal_mode=WAL')
                self._local_conn.execute('PRAGMA foreign_keys=ON')
                # Runtime schema guard: always upgrade old local databases before
                # repositories can run INSERT/UPDATE statements. This prevents
                # errors such as: table invoices has no column named warehouse_id.
                try:
                    from .schema_manager import apply_common_schema
                    apply_common_schema(self._local_conn)
                except Exception as exc:
                    print(f"⚠️ فشل فحص/ترقية بنية قاعدة البيانات: {exc}")
                    raise
            return self._local_conn
        else:
            return None

    def execute(self, sql: str, params=()):
        if self.mode != "client":
            conn = self.get_connection()
            return conn.execute(sql, params)
        else:
            raise NotImplementedError("Use REST client methods for remote mode")

    def executemany(self, sql: str, params_list):
        if self.mode != "client":
            conn = self.get_connection()
            return conn.executemany(sql, params_list)
        else:
            raise NotImplementedError("Use REST client methods for remote mode")

    def commit(self):
        if self.mode != "client":
            self.get_connection().commit()

    def rollback(self):
        if self.mode != "client":
            self.get_connection().rollback()

    def begin(self):
        if self.mode != "client":
            self.execute("BEGIN TRANSACTION")

    def close(self):
        if self._local_conn:
            self._local_conn.close()
            self._local_conn = None


    def _assert_unique_barcode(self, user_id, barcode, item_id=None):
        barcode = str(barcode).strip() if barcode is not None else ''
        if not barcode:
            return
        conn = self.get_connection()
        params = [user_id, barcode]
        sql = "SELECT id, name FROM items WHERE user_id=? AND barcode=? AND deleted_at IS NULL"
        if item_id is not None:
            sql += " AND id<>?"
            params.append(item_id)
        row = conn.execute(sql, params).fetchone()
        if row:
            raise ValueError(f"الباركود '{barcode}' مستخدم بالفعل للمادة: {row['name']}")

    def _log_audit_local(self, user_id, username, action, table_name, record_id, details, ip='127.0.0.1'):
        if self.mode == "client":
            return
        conn = self.get_connection()
        now = datetime.datetime.now().isoformat()
        conn.execute('''
            INSERT INTO audit_log (user_id, username, action, table_name, record_id, details, ip_address, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, username, action, table_name, record_id, details, ip, now))
        conn.commit()

    # ------------------- CRUD للمواد مع Pagination -------------------
    def get_items(self, search: str = None, limit: int = None, offset: int = None) -> Tuple[List[Dict], int]:
        if self.is_remote():
            return self._rest_client.get_items(search, limit, offset)
        from auth.session import UserSession
        uid = UserSession.get_current_user_id()
        conn = self.get_connection()
        count_sql = "SELECT COUNT(*) FROM items WHERE user_id = ? AND deleted_at IS NULL"
        count_params = [uid]
        if search:
            count_sql += " AND (name LIKE ? OR barcode LIKE ?)"
            count_params.extend([f"%{search}%", f"%{search}%"])
        total = conn.execute(count_sql, count_params).fetchone()[0]
        query = """
            SELECT i.*, c.name as category_name,
                   COALESCE((
                       SELECT SUM(CASE
                           WHEN movement_type IN ('opening','purchase','adjustment','production_out','sales_return') THEN CAST(quantity AS REAL)
                           WHEN movement_type IN ('sale','production_consume') THEN -CAST(quantity AS REAL)
                           ELSE 0 END)
                       FROM inventory_movements
                       WHERE item_id = i.id AND user_id = i.user_id
                   ), CAST(COALESCE(i.quantity, '0') AS REAL)) AS available,
                   COALESCE((
                       SELECT SUM(CAST(quantity AS REAL))
                       FROM inventory_movements
                       WHERE item_id = i.id AND user_id = i.user_id AND movement_type = 'opening'
                   ), CAST(COALESCE(i.quantity, '0') AS REAL)) AS opening_quantity
            FROM items i 
            LEFT JOIN categories c ON i.category_id = c.id 
            WHERE i.user_id = ? AND i.deleted_at IS NULL
        """
        params = [uid]
        if search:
            query += " AND (i.name LIKE ? OR i.barcode LIKE ?)"
            params.extend([f"%{search}%", f"%{search}%"])
        query += " ORDER BY i.name"
        if limit is not None:
            query += " LIMIT ?"
            params.append(limit)
        if offset is not None:
            query += " OFFSET ?"
            params.append(offset)
        rows = conn.execute(query, params).fetchall()
        return [dict(row) for row in rows], total

    def add_item(self, data: Dict) -> int:
        if self.is_remote():
            return self._rest_client.add_item(data)
        from auth.session import UserSession
        uid = UserSession.get_current_user_id()
        conn = self.get_connection()
        def to_str(value):
            if isinstance(value, Decimal):
                return str(value)
            return value
        self._assert_unique_barcode(uid, data.get('barcode'))
        cursor = conn.execute('''
            INSERT INTO items (user_id, name, category_id, item_type, purchase_price, selling_price, quantity, unit, average_cost, barcode, reorder_level)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
        ''', (
            uid, data['name'], data.get('category_id'), data.get('item_type', 'مخزون'),
            to_str(data.get('purchase_price', 0)), to_str(data.get('selling_price', 0)),
            to_str(data.get('quantity', 0)), data.get('unit', ''), to_str(data.get('average_cost', 0)),
            data.get('barcode'), to_str(data.get('reorder_level', 0))
        ))
        item_id = cursor.lastrowid
        self._sync_opening_inventory(item_id, uid, data.get('quantity', 0), data.get('average_cost', data.get('purchase_price', 0)))
        conn.commit()
        return item_id

    def update_item(self, item_id: int, data: Dict):
        if self.is_remote():
            self._rest_client.update_item(item_id, data)
            return
        from auth.session import UserSession
        uid = UserSession.get_current_user_id()
        conn = self.get_connection()
        def to_str(value):
            if isinstance(value, Decimal):
                return str(value)
            return value
        current_opening = self._get_opening_quantity(item_id, uid)
        new_opening = Decimal(str(data.get('quantity', 0) or 0))
        if current_opening != new_opening and self._has_non_opening_item_movements(item_id, uid):
            raise ValueError("لا يمكن تعديل الكمية الافتتاحية بعد وجود حركات بيع/شراء/تصنيع/تسوية. استخدم تسوية مخزون بدل تعديل الافتتاحي.")
        self._assert_unique_barcode(uid, data.get('barcode'), item_id=item_id)
        conn.execute('''
            UPDATE items SET name=?, category_id=?, item_type=?, purchase_price=?, selling_price=?, quantity=?, unit=?, average_cost=?, barcode=?, reorder_level=?
            WHERE id=? AND user_id=? AND deleted_at IS NULL
        ''', (
            data['name'], data.get('category_id'), data.get('item_type'),
            to_str(data.get('purchase_price', 0)), to_str(data.get('selling_price', 0)),
            to_str(data.get('quantity', 0)), data.get('unit', ''), to_str(data.get('average_cost', 0)),
            data.get('barcode'), to_str(data.get('reorder_level', 0)), item_id, uid
        ))
        self._sync_opening_inventory(item_id, uid, data.get('quantity', 0), data.get('average_cost', data.get('purchase_price', 0)))
        conn.commit()

    def delete_item(self, item_id: int):
        if self.is_remote():
            self._rest_client.delete_item(item_id)
            return
        from auth.session import UserSession
        uid = UserSession.get_current_user_id()
        conn = self.get_connection()
        usage = self._get_item_usage_summary(item_id, uid)
        if usage['blocking_total'] > 0:
            details = ', '.join(f"{k}={v}" for k, v in usage.items() if k != 'blocking_total' and v)
            raise ValueError(f"لا يمكن حذف المادة لأنها مستخدمة في عمليات سابقة ({details}).")
        now = datetime.datetime.now().isoformat()
        conn.execute("UPDATE items SET deleted_at=?, name = name || ' [محذوف #' || id || ']' WHERE id=? AND user_id=? AND deleted_at IS NULL", (now, item_id, uid))
        conn.commit()

    def get_item_by_id(self, item_id: int) -> Optional[Dict]:
        if self.is_remote():
            items, _ = self.get_items()
            for it in items:
                if it['id'] == item_id:
                    return it
            return None
        from auth.session import UserSession
        uid = UserSession.get_current_user_id()
        conn = self.get_connection()
        row = conn.execute("""
            SELECT i.*, c.name as category_name,
                   COALESCE((
                       SELECT SUM(CASE
                           WHEN movement_type IN ('opening','purchase','adjustment','production_out','sales_return') THEN CAST(quantity AS REAL)
                           WHEN movement_type IN ('sale','production_consume') THEN -CAST(quantity AS REAL)
                           ELSE 0 END)
                       FROM inventory_movements
                       WHERE item_id = i.id AND user_id = i.user_id
                   ), CAST(COALESCE(i.quantity, '0') AS REAL)) AS available,
                   COALESCE((
                       SELECT SUM(CAST(quantity AS REAL))
                       FROM inventory_movements
                       WHERE item_id = i.id AND user_id = i.user_id AND movement_type = 'opening'
                   ), CAST(COALESCE(i.quantity, '0') AS REAL)) AS opening_quantity
            FROM items i
            LEFT JOIN categories c ON i.category_id = c.id
            WHERE i.id=? AND (? IS NULL OR i.user_id=?)
        """, (item_id, uid, uid)).fetchone()
        return dict(row) if row else None

    # ------------------- CRUD للعملاء مع Pagination -------------------
    def get_customers(self, search: str = None, limit: int = None, offset: int = None) -> Tuple[List[Dict], int]:
        if self.is_remote():
            return self._rest_client.get_customers(search, limit, offset)
        from auth.session import UserSession
        uid = UserSession.get_current_user_id()
        conn = self.get_connection()
        count_sql = "SELECT COUNT(*) FROM customers WHERE user_id = ?"
        count_params = [uid]
        if search:
            count_sql += " AND (name LIKE ? OR phone LIKE ?)"
            count_params.extend([f"%{search}%", f"%{search}%"])
        total = conn.execute(count_sql, count_params).fetchone()[0]
        query = "SELECT * FROM customers WHERE user_id = ?"
        params = [uid]
        if search:
            query += " AND (name LIKE ? OR phone LIKE ?)"
            params.extend([f"%{search}%", f"%{search}%"])
        query += " ORDER BY name"
        if limit is not None:
            query += " LIMIT ?"
            params.append(limit)
        if offset is not None:
            query += " OFFSET ?"
            params.append(offset)
        rows = conn.execute(query, params).fetchall()
        return [dict(row) for row in rows], total

    def add_customer(self, data: Dict) -> int:
        if self.is_remote():
            return self._rest_client.add_customer(data)
        from auth.session import UserSession
        uid = UserSession.get_current_user_id()
        conn = self.get_connection()
        def to_str(value):
            if isinstance(value, Decimal):
                return str(value)
            return value
        cursor = conn.execute('''
            INSERT INTO customers (user_id, name, phone, address, balance)
            VALUES (?,?,?,?,?)
        ''', (uid, data['name'], data.get('phone', ''), data.get('address', ''), to_str(data.get('balance', '0'))))
        conn.commit()
        return cursor.lastrowid

    def update_customer(self, customer_id: int, data: Dict):
        if self.is_remote():
            self._rest_client.update_customer(customer_id, data)
            return
        from auth.session import UserSession
        uid = UserSession.get_current_user_id()
        conn = self.get_connection()
        def to_str(value):
            if isinstance(value, Decimal):
                return str(value)
            return value
        conn.execute('''
            UPDATE customers SET name=?, phone=?, address=?, balance=?
            WHERE id=? AND user_id=?
        ''', (data['name'], data.get('phone', ''), data.get('address', ''), to_str(data.get('balance', '0')), customer_id, uid))
        conn.commit()

    def delete_customer(self, customer_id: int):
        if self.is_remote():
            self._rest_client.delete_customer(customer_id)
            return
        from auth.session import UserSession
        uid = UserSession.get_current_user_id()
        conn = self.get_connection()
        conn.execute("DELETE FROM customers WHERE id=? AND user_id=?", (customer_id, uid))
        conn.commit()

    # ------------------- CRUD للموردين مع Pagination -------------------
    def get_suppliers(self, search: str = None, limit: int = None, offset: int = None) -> Tuple[List[Dict], int]:
        if self.is_remote():
            return self._rest_client.get_suppliers(search, limit, offset)
        from auth.session import UserSession
        uid = UserSession.get_current_user_id()
        conn = self.get_connection()
        count_sql = "SELECT COUNT(*) FROM suppliers WHERE user_id = ?"
        count_params = [uid]
        if search:
            count_sql += " AND (name LIKE ? OR phone LIKE ?)"
            count_params.extend([f"%{search}%", f"%{search}%"])
        total = conn.execute(count_sql, count_params).fetchone()[0]
        query = "SELECT * FROM suppliers WHERE user_id = ?"
        params = [uid]
        if search:
            query += " AND (name LIKE ? OR phone LIKE ?)"
            params.extend([f"%{search}%", f"%{search}%"])
        query += " ORDER BY name"
        if limit is not None:
            query += " LIMIT ?"
            params.append(limit)
        if offset is not None:
            query += " OFFSET ?"
            params.append(offset)
        rows = conn.execute(query, params).fetchall()
        return [dict(row) for row in rows], total

    def add_supplier(self, data: Dict) -> int:
        if self.is_remote():
            return self._rest_client.add_supplier(data)
        from auth.session import UserSession
        uid = UserSession.get_current_user_id()
        conn = self.get_connection()
        def to_str(value):
            if isinstance(value, Decimal):
                return str(value)
            return value
        cursor = conn.execute('''
            INSERT INTO suppliers (user_id, name, phone, address, balance)
            VALUES (?,?,?,?,?)
        ''', (uid, data['name'], data.get('phone', ''), data.get('address', ''), to_str(data.get('balance', '0'))))
        conn.commit()
        return cursor.lastrowid

    def update_supplier(self, supplier_id: int, data: Dict):
        if self.is_remote():
            self._rest_client.update_supplier(supplier_id, data)
            return
        from auth.session import UserSession
        uid = UserSession.get_current_user_id()
        conn = self.get_connection()
        def to_str(value):
            if isinstance(value, Decimal):
                return str(value)
            return value
        conn.execute('''
            UPDATE suppliers SET name=?, phone=?, address=?, balance=?
            WHERE id=? AND user_id=?
        ''', (data['name'], data.get('phone', ''), data.get('address', ''), to_str(data.get('balance', '0')), supplier_id, uid))
        conn.commit()

    def delete_supplier(self, supplier_id: int):
        if self.is_remote():
            self._rest_client.delete_supplier(supplier_id)
            return
        from auth.session import UserSession
        uid = UserSession.get_current_user_id()
        conn = self.get_connection()
        conn.execute("DELETE FROM suppliers WHERE id=? AND user_id=?", (supplier_id, uid))
        conn.commit()

    # ------------------- CRUD للفواتير مع Pagination -------------------
    def get_invoices(self, search: str = None, inv_type: str = None,
                     start_date: str = None, end_date: str = None,
                     customer_id: int = None, supplier_id: int = None,
                     limit: int = None, offset: int = None) -> Tuple[List[Dict], int]:
        if self.is_remote():
            return self._rest_client.get_invoices(inv_type, start_date, end_date, limit, offset)
        from auth.session import UserSession
        uid = UserSession.get_current_user_id()
        conn = self.get_connection()
        count_sql = """
            SELECT COUNT(*)
            FROM invoices i
            LEFT JOIN customers c ON i.customer_id = c.id
            LEFT JOIN suppliers s ON i.supplier_id = s.id
            LEFT JOIN branches b ON i.branch_id = b.id
            WHERE i.user_id = ? AND i.deleted_at IS NULL
        """
        count_params = [uid]
        if search:
            count_sql += " AND (i.reference LIKE ? OR c.name LIKE ? OR s.name LIKE ?)"
            search_param = f"%{search}%"
            count_params.extend([search_param, search_param, search_param])
        if inv_type and inv_type in ('sale', 'purchase'):
            count_sql += " AND i.type = ?"
            count_params.append(inv_type)
        if start_date:
            count_sql += " AND i.date >= ?"
            count_params.append(start_date)
        if end_date:
            count_sql += " AND i.date <= ?"
            count_params.append(end_date)
        if customer_id:
            count_sql += " AND i.customer_id = ?"
            count_params.append(customer_id)
        if supplier_id:
            count_sql += " AND i.supplier_id = ?"
            count_params.append(supplier_id)
        total = conn.execute(count_sql, count_params).fetchone()[0]
        query = """
            SELECT i.*, c.name as customer_name, s.name as supplier_name, b.name as branch_name
            FROM invoices i
            LEFT JOIN customers c ON i.customer_id = c.id
            LEFT JOIN suppliers s ON i.supplier_id = s.id
            LEFT JOIN branches b ON i.branch_id = b.id
            WHERE i.user_id = ? AND i.deleted_at IS NULL
        """
        params = [uid]
        if search:
            query += " AND (i.reference LIKE ? OR c.name LIKE ? OR s.name LIKE ?)"
            params.extend([search_param, search_param, search_param])
        if inv_type and inv_type in ('sale', 'purchase'):
            query += " AND i.type = ?"
            params.append(inv_type)
        if start_date:
            query += " AND i.date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND i.date <= ?"
            params.append(end_date)
        if customer_id:
            query += " AND i.customer_id = ?"
            params.append(customer_id)
        if supplier_id:
            query += " AND i.supplier_id = ?"
            params.append(supplier_id)
        query += " ORDER BY i.id DESC"
        if limit is not None:
            query += " LIMIT ?"
            params.append(limit)
        if offset is not None:
            query += " OFFSET ?"
            params.append(offset)
        rows = conn.execute(query, params).fetchall()
        return [dict(row) for row in rows], total

    def get_invoice_by_id(self, invoice_id: int) -> Optional[Dict]:
        if self.is_remote():
            return self._rest_client.get_invoice_by_id(invoice_id)
        conn = self.get_connection()
        row = conn.execute("SELECT * FROM invoices WHERE id=?", (invoice_id,)).fetchone()
        if not row:
            return None
        inv = dict(row)
        lines = conn.execute("SELECT * FROM invoice_lines WHERE invoice_id=?", (invoice_id,)).fetchall()
        inv['lines'] = [dict(line) for line in lines]
        return inv

    def add_invoice(self, data: Dict) -> int:
        if self.is_remote():
            return self._rest_client.add_invoice(data)
        from auth.session import UserSession
        uid = UserSession.get_current_user_id()
        conn = self.get_connection()
        self.begin()
        try:
            cursor = conn.execute('''
                INSERT INTO invoices (user_id, type, customer_id, supplier_id, date, reference, notes, total, paid, status, exchange_rate_to_usd, original_currency, warehouse_id, branch_id, cashbox_id, bank_account_id, payment_method, shift_id)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ''', (
                uid, data['type'], data.get('customer_id'), data.get('supplier_id'),
                data['date'], data.get('reference', ''), data.get('notes', ''),
                str(data['total']), str(data['paid_amount']), 'active',
                data.get('exchange_rate_to_usd', 1.0), data.get('original_currency', 'USD'),
                data.get('warehouse_id'), data.get('branch_id'), data.get('cashbox_id'),
                data.get('bank_account_id'), data.get('payment_method', 'cash'), data.get('shift_id')
            ))
            invoice_id = cursor.lastrowid
            for line in data['lines']:
                conv_factor = line.get('conversion_factor', Decimal('1'))
                if conv_factor <= 0:
                    conv_factor = Decimal('1')
                base_qty = line.get('base_qty', line['quantity'])
                unit_cost = line['unit_price']
                cursor2 = conn.execute('''
                    INSERT INTO invoice_lines (invoice_id, item_id, quantity, unit_price, total, unit, quantity_in_base, unit_cost, cost_amount, conversion_factor)
                    VALUES (?,?,?,?,?,?,?,?,?,?)
                ''', (
                    invoice_id, line['item_id'], str(line['quantity']),
                    str(unit_cost), str(line['total']), line.get('unit', ''),
                    str(base_qty), str(unit_cost), '0', str(conv_factor)
                ))
                line_id = cursor2.lastrowid
                if data['type'] == 'purchase':
                    unit_cost_base = unit_cost / conv_factor
                    self._record_inventory_movement(line['item_id'], 'purchase', base_qty, unit_cost_base, invoice_id)
                    cost_amt = unit_cost_base * base_qty
                    conn.execute("UPDATE invoice_lines SET cost_amount=? WHERE id=?", (str(cost_amt), line_id))
                else:
                    item = conn.execute("SELECT CAST(average_cost AS TEXT) as avg_cost FROM items WHERE id=?", (line['item_id'],)).fetchone()
                    avg_cost = Decimal(str(item['avg_cost'])) if item else Decimal('0')
                    cost_amt = base_qty * avg_cost
                    conn.execute("UPDATE invoice_lines SET cost_amount=? WHERE id=?", (str(cost_amt), line_id))
                    self._record_inventory_movement(line['item_id'], 'sale', base_qty, unit_cost, invoice_id)
            if data['type'] == 'sale' and data.get('customer_id'):
                self._update_customer_balance(data['customer_id'], Decimal(str(data['total'])) - Decimal(str(data['paid_amount'])))
            elif data['type'] == 'purchase' and data.get('supplier_id'):
                self._update_supplier_balance(data['supplier_id'], Decimal(str(data['total'])) - Decimal(str(data['paid_amount'])))
            if Decimal(str(data['paid_amount'])) > 0:
                if data['type'] == 'sale':
                    self._update_cash_balance(Decimal(str(data['paid_amount'])), add=True)
                else:
                    self._update_cash_balance(Decimal(str(data['paid_amount'])), add=False)
            self.commit()
            return invoice_id
        except Exception as e:
            self.rollback()
            raise e

    def update_invoice(self, invoice_id: int, data: Dict):
        """تحديث الفاتورة مع الحفاظ على رقمها، وعكس الأثر المالي/المخزني القديم داخل معاملة واحدة."""
        if self.is_remote():
            self._rest_client.update_invoice(invoice_id, data)
            return
        inv = self.get_invoice_by_id(invoice_id)
        if not inv:
            raise ValueError("الفاتورة غير موجودة")
        if self._invoice_has_vouchers(invoice_id):
            raise ValueError("لا يمكن تعديل فاتورة مرتبطة بسندات. احذف أو عدّل السندات أولاً.")
        conn = self.get_connection()
        self.begin()
        try:
            old_total = Decimal(str(inv.get('total', 0)))
            old_paid = Decimal(str(inv.get('paid', 0)))
            if inv['type'] == 'sale' and inv.get('customer_id'):
                self._update_customer_balance(inv['customer_id'], -(old_total - old_paid))
            elif inv['type'] == 'purchase' and inv.get('supplier_id'):
                self._update_supplier_balance(inv['supplier_id'], -(old_total - old_paid))
            if old_paid > 0:
                self._update_cash_balance(old_paid, add=(inv['type'] == 'purchase'))

            old_item_ids = [row['item_id'] for row in conn.execute("SELECT item_id FROM invoice_lines WHERE invoice_id=?", (invoice_id,)).fetchall()]
            conn.execute("DELETE FROM inventory_movements WHERE reference_id=? AND movement_type IN ('purchase','sale')", (invoice_id,))
            conn.execute("DELETE FROM invoice_lines WHERE invoice_id=?", (invoice_id,))
            conn.execute('''
                UPDATE invoices SET type=?, customer_id=?, supplier_id=?, date=?, reference=?, notes=?, total=?, paid=?,
                    status='active', exchange_rate_to_usd=?, original_currency=?, warehouse_id=?, branch_id=?, deleted_at=NULL
                WHERE id=?
            ''', (
                data['type'], data.get('customer_id'), data.get('supplier_id'), data['date'],
                data.get('reference', ''), data.get('notes', ''), str(data['total']),
                str(data.get('paid_amount', data.get('paid', 0))), data.get('exchange_rate_to_usd', 1.0),
                data.get('original_currency', 'USD'), data.get('warehouse_id'), data.get('branch_id'), invoice_id
            ))

            new_item_ids = []
            for line in data['lines']:
                conv_factor = Decimal(str(line.get('conversion_factor', 1)))
                if conv_factor <= 0:
                    conv_factor = Decimal('1')
                base_qty = Decimal(str(line.get('base_qty', line['quantity'])))
                unit_cost = Decimal(str(line['unit_price']))
                cursor2 = conn.execute('''
                    INSERT INTO invoice_lines (invoice_id, item_id, quantity, unit_price, total, unit, quantity_in_base, unit_cost, cost_amount, conversion_factor)
                    VALUES (?,?,?,?,?,?,?,?,?,?)
                ''', (
                    invoice_id, line['item_id'], str(line['quantity']), str(unit_cost), str(line['total']),
                    line.get('unit', ''), str(base_qty), str(unit_cost), '0', str(conv_factor)
                ))
                line_id = cursor2.lastrowid
                new_item_ids.append(line['item_id'])
                if data['type'] == 'purchase':
                    unit_cost_base = unit_cost / conv_factor
                    self._record_inventory_movement(line['item_id'], 'purchase', base_qty, unit_cost_base, invoice_id)
                    cost_amt = unit_cost_base * base_qty
                else:
                    item = conn.execute("SELECT CAST(average_cost AS TEXT) as avg_cost FROM items WHERE id=?", (line['item_id'],)).fetchone()
                    avg_cost = Decimal(str(item['avg_cost'])) if item else Decimal('0')
                    cost_amt = base_qty * avg_cost
                    self._record_inventory_movement(line['item_id'], 'sale', base_qty, unit_cost, invoice_id)
                conn.execute("UPDATE invoice_lines SET cost_amount=? WHERE id=?", (str(cost_amt), line_id))

            for item_id in set(old_item_ids + new_item_ids):
                self._update_item_quantity(item_id)
                self._recalculate_average_cost(item_id)

            new_total = Decimal(str(data['total']))
            new_paid = Decimal(str(data.get('paid_amount', data.get('paid', 0))))
            if data['type'] == 'sale' and data.get('customer_id'):
                self._update_customer_balance(data['customer_id'], new_total - new_paid)
            elif data['type'] == 'purchase' and data.get('supplier_id'):
                self._update_supplier_balance(data['supplier_id'], new_total - new_paid)
            if new_paid > 0:
                self._update_cash_balance(new_paid, add=(data['type'] == 'sale'))
            self.commit()
        except Exception:
            self.rollback()
            raise

    def delete_invoice(self, invoice_id: int):
        if self.is_remote():
            self._rest_client.delete_invoice(invoice_id)
            return
        inv = self.get_invoice_by_id(invoice_id)
        if not inv:
            return
        if self._invoice_has_vouchers(invoice_id):
            raise ValueError("لا يمكن حذف فاتورة مرتبطة بسندات. احذف السندات أولاً.")
        conn = self.get_connection()
        self.begin()
        try:
            lines = conn.execute("SELECT * FROM invoice_lines WHERE invoice_id=?", (invoice_id,)).fetchall()
            for line in lines:
                item_id = line['item_id']
                base_qty = Decimal(str(line['quantity_in_base']))
                conn.execute('''
                    DELETE FROM inventory_movements
                    WHERE item_id = ? AND reference_id = ? AND movement_type IN ('purchase', 'sale')
                ''', (item_id, invoice_id))
                self._update_item_quantity(item_id)
                self._recalculate_average_cost(item_id)
            total = Decimal(str(inv['total']))
            paid = Decimal(str(inv['paid']))
            if inv['type'] == 'sale' and inv.get('customer_id'):
                self._update_customer_balance(inv['customer_id'], -(total - paid))
            elif inv['type'] == 'purchase' and inv.get('supplier_id'):
                self._update_supplier_balance(inv['supplier_id'], -(total - paid))
            if paid > 0:
                if inv['type'] == 'sale':
                    self._update_cash_balance(paid, add=False)
                else:
                    self._update_cash_balance(paid, add=True)
            conn.execute("UPDATE invoices SET deleted_at = datetime('now') WHERE id=?", (invoice_id,))
            self.commit()
        except Exception as e:
            self.rollback()
            raise e


    # ------------------- Accounting integrity guards -------------------
    def _invoice_has_vouchers(self, invoice_id: int) -> bool:
        conn = self.get_connection()
        row = conn.execute("SELECT COUNT(*) AS cnt FROM vouchers WHERE invoice_id=?", (invoice_id,)).fetchone()
        return bool(row and row['cnt'])

    def _validate_voucher_data(self, data: Dict, exclude_voucher_id: int = None):
        vtype = data.get('type')
        if vtype not in ('receipt', 'payment', 'expense'):
            raise ValueError("نوع السند غير صالح")
        amount = Decimal(str(data.get('amount', 0)))
        if amount <= 0:
            raise ValueError("مبلغ السند يجب أن يكون أكبر من صفر")
        customer_id = data.get('customer_id')
        supplier_id = data.get('supplier_id')
        invoice_id = data.get('invoice_id')
        if vtype == 'receipt':
            if not customer_id or supplier_id:
                raise ValueError("سند القبض يجب أن يرتبط بعميل فقط")
        elif vtype == 'payment':
            if not supplier_id or customer_id:
                raise ValueError("سند الدفع يجب أن يرتبط بمورد فقط")
        elif vtype == 'expense':
            if invoice_id:
                raise ValueError("سند المصروف لا يجب ربطه بفاتورة")
            if customer_id or supplier_id:
                raise ValueError("سند المصروف لا يجب ربطه بعميل أو مورد")
        if not invoice_id:
            return
        inv = self.get_invoice_by_id(invoice_id)
        if not inv or inv.get('deleted_at'):
            raise ValueError("الفاتورة المرتبطة غير موجودة أو محذوفة")
        if vtype == 'receipt' and inv.get('type') != 'sale':
            raise ValueError("سند القبض لا يرتبط إلا بفاتورة بيع")
        if vtype == 'payment' and inv.get('type') != 'purchase':
            raise ValueError("سند الدفع لا يرتبط إلا بفاتورة شراء")
        if vtype == 'receipt' and customer_id and inv.get('customer_id') != customer_id:
            raise ValueError("العميل في السند لا يطابق عميل الفاتورة")
        if vtype == 'payment' and supplier_id and inv.get('supplier_id') != supplier_id:
            raise ValueError("المورد في السند لا يطابق مورد الفاتورة")
        total = Decimal(str(inv.get('total', 0)))
        paid = Decimal(str(inv.get('paid', 0)))
        old_amount = Decimal('0')
        if exclude_voucher_id is not None:
            old = self.get_voucher_by_id(exclude_voucher_id)
            if old and old.get('invoice_id') == invoice_id:
                old_amount = Decimal(str(old.get('amount', 0)))
        remaining = total - (paid - old_amount)
        if amount > remaining:
            raise ValueError(f"مبلغ السند يتجاوز المتبقي على الفاتورة ({remaining})")

    # ------------------- السندات مع Pagination -------------------
    def get_vouchers(self, vtype: str = None, limit: int = None, offset: int = None) -> Tuple[List[Dict], int]:
        if self.is_remote():
            return self._rest_client.get_vouchers(vtype, limit, offset)
        from auth.session import UserSession
        uid = UserSession.get_current_user_id()
        conn = self.get_connection()
        count_sql = "SELECT COUNT(*) FROM vouchers WHERE user_id = ?"
        count_params = [uid]
        if vtype and vtype in ('receipt', 'payment', 'expense'):
            count_sql += " AND type = ?"
            count_params.append(vtype)
        total = conn.execute(count_sql, count_params).fetchone()[0]
        query = "SELECT v.*, b.name AS branch_name, c.name AS cashbox_name, ba.bank_name AS bank_name, ba.account_name AS bank_account_name FROM vouchers v LEFT JOIN branches b ON b.id=v.branch_id LEFT JOIN cashboxes c ON c.id=v.cashbox_id LEFT JOIN bank_accounts ba ON ba.id=v.bank_account_id WHERE v.user_id = ?"
        params = [uid]
        if vtype and vtype in ('receipt', 'payment', 'expense'):
            query += " AND v.type = ?"
            params.append(vtype)
        query += " ORDER BY id DESC"
        if limit is not None:
            query += " LIMIT ?"
            params.append(limit)
        if offset is not None:
            query += " OFFSET ?"
            params.append(offset)
        rows = conn.execute(query, params).fetchall()
        return [dict(row) for row in rows], total

    def get_voucher_by_id(self, voucher_id: int) -> Optional[Dict]:
        if self.is_remote():
            return self._rest_client.get_voucher(voucher_id)
        conn = self.get_connection()
        row = conn.execute("SELECT * FROM vouchers WHERE id=?", (voucher_id,)).fetchone()
        return dict(row) if row else None

    def add_voucher(self, data: Dict) -> int:
        if self.is_remote():
            return self._rest_client.add_voucher(data)
        from auth.session import UserSession
        uid = UserSession.get_current_user_id()
        conn = self.get_connection()
        self._validate_voucher_data(data)
        self.begin()
        try:
            cursor = conn.execute('''
                INSERT INTO vouchers (user_id, type, date, amount, description, reference, customer_id, supplier_id, invoice_id, exchange_rate_to_usd, original_currency, branch_id, cashbox_id, bank_account_id, payment_method)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ''', (
                uid, data['type'], data['date'], str(data['amount']),
                data.get('description', ''), data.get('reference', ''),
                data.get('customer_id'), data.get('supplier_id'), data.get('invoice_id'),
                data.get('exchange_rate_to_usd', 1.0), data.get('original_currency', 'USD'), data.get('branch_id'),
                data.get('cashbox_id'), data.get('bank_account_id'), data.get('payment_method', 'cash')
            ))
            voucher_id = cursor.lastrowid
            amount = Decimal(str(data['amount']))
            if data['type'] == 'receipt':
                self._update_cash_balance(amount, add=True)
            elif data['type'] in ('payment', 'expense'):
                self._update_cash_balance(amount, add=False)
            if data.get('customer_id'):
                self._update_customer_balance(data['customer_id'], -amount)
            elif data.get('supplier_id'):
                self._update_supplier_balance(data['supplier_id'], -amount)
            if data.get('invoice_id'):
                self._update_invoice_paid(data['invoice_id'], amount, add=True)
            self.commit()
            return voucher_id
        except Exception as e:
            self.rollback()
            raise e

    def delete_voucher(self, voucher_id: int):
        if self.is_remote():
            self._rest_client.delete_voucher(voucher_id)
            return
        conn = self.get_connection()
        row = conn.execute("SELECT * FROM vouchers WHERE id=?", (voucher_id,)).fetchone()
        if not row:
            return
        voucher = dict(row)
        self.begin()
        try:
            amount = Decimal(str(voucher['amount']))
            if voucher['type'] == 'receipt':
                self._update_cash_balance(amount, add=False)
            elif voucher['type'] in ('payment', 'expense'):
                self._update_cash_balance(amount, add=True)
            if voucher.get('customer_id'):
                self._update_customer_balance(voucher['customer_id'], amount)
            elif voucher.get('supplier_id'):
                self._update_supplier_balance(voucher['supplier_id'], amount)
            if voucher.get('invoice_id'):
                self._update_invoice_paid(voucher['invoice_id'], amount, add=False)
            conn.execute("DELETE FROM vouchers WHERE id=?", (voucher_id,))
            self.commit()
        except Exception as e:
            self.rollback()
            raise e

    def update_voucher(self, voucher_id: int, data: Dict):
        if self.is_remote():
            self._rest_client.update_voucher(voucher_id, data)
            return
        if not self.get_voucher_by_id(voucher_id):
            raise ValueError("السند غير موجود")
        self._validate_voucher_data(data, exclude_voucher_id=voucher_id)
        self.delete_voucher(voucher_id)
        self.add_voucher(data)

    # ------------------- دوال مساعدة داخلية -------------------
    def _get_opening_quantity(self, item_id, user_id):
        conn = self.get_connection()
        row = conn.execute("""
            SELECT COALESCE(SUM(CAST(quantity AS REAL)), 0) AS qty
            FROM inventory_movements
            WHERE item_id=? AND user_id=? AND movement_type='opening'
        """, (item_id, user_id)).fetchone()
        return Decimal(str(row['qty'] if row and row['qty'] is not None else 0))

    def _has_non_opening_item_movements(self, item_id, user_id):
        conn = self.get_connection()
        row = conn.execute("""
            SELECT COUNT(*) AS cnt
            FROM inventory_movements
            WHERE item_id=? AND user_id=? AND movement_type <> 'opening'
        """, (item_id, user_id)).fetchone()
        return bool(row and row['cnt'])

    def _get_item_usage_summary(self, item_id, user_id):
        conn = self.get_connection()
        def count(sql, params):
            row = conn.execute(sql, params).fetchone()
            return int(row[0] if row else 0)
        summary = {
            'invoice_lines': count("SELECT COUNT(*) FROM invoice_lines WHERE item_id=?", (item_id,)),
            'inventory_movements': count("SELECT COUNT(*) FROM inventory_movements WHERE item_id=? AND user_id=? AND movement_type <> 'opening'", (item_id, user_id)),
            'bom_products': count("SELECT COUNT(*) FROM bom WHERE product_id=? AND user_id=?", (item_id, user_id)),
            'bom_lines': count("SELECT COUNT(*) FROM bom_lines WHERE item_id=?", (item_id,)),
            'production_orders': count("SELECT COUNT(*) FROM production_orders WHERE product_id=? AND user_id=?", (item_id, user_id)),
            'production_consumptions': count("SELECT COUNT(*) FROM production_consumptions WHERE item_id=?", (item_id,)),
            'production_outputs': count("SELECT COUNT(*) FROM production_outputs WHERE item_id=?", (item_id,)),
        }
        summary['blocking_total'] = sum(summary.values())
        return summary

    def _sync_opening_inventory(self, item_id, user_id, quantity, unit_cost):
        """Create/update the opening stock movement for an item.

        Inventory balance is derived from inventory_movements. The items.quantity
        column is only a cached balance.  Without an opening movement, the
        opening quantity entered in ItemDialog is ignored by stock valuation and
        future recalculations.
        """
        if self.mode == "client":
            return
        conn = self.get_connection()
        qty = Decimal(str(quantity or 0))
        cost = Decimal(str(unit_cost or 0))
        conn.execute(
            "DELETE FROM inventory_movements WHERE item_id=? AND user_id=? AND movement_type='opening' AND reference_id IS NULL",
            (item_id, user_id)
        )
        if qty != 0:
            now = datetime.datetime.now().isoformat()
            conn.execute('''
                INSERT INTO inventory_movements (item_id, user_id, movement_type, quantity, unit_cost, reference_id, movement_date)
                VALUES (?,?,?,?,?,?,?)
            ''', (item_id, user_id, 'opening', str(qty), str(cost), None, now))
        self._update_item_quantity(item_id)
        self._recalculate_average_cost(item_id)

    def _record_inventory_movement(self, item_id, movement_type, quantity, unit_cost, reference_id):
        from auth.session import UserSession
        uid = UserSession.get_current_user_id()
        conn = self.get_connection()
        now = datetime.datetime.now().isoformat()
        conn.execute('''
            INSERT INTO inventory_movements (item_id, user_id, movement_type, quantity, unit_cost, reference_id, movement_date)
            VALUES (?,?,?,?,?,?,?)
        ''', (item_id, uid, movement_type, str(quantity), str(unit_cost), reference_id, now))
        self._update_item_quantity(item_id)
        if movement_type in ('opening', 'purchase', 'adjustment', 'production_out'):
            self._recalculate_average_cost(item_id)

    def _update_item_quantity(self, item_id):
        conn = self.get_connection()
        cur = conn.execute('''
            SELECT SUM(
                CASE 
                    WHEN movement_type IN ('opening','purchase','adjustment','production_out','sales_return') 
                    THEN CAST(quantity AS REAL)
                    WHEN movement_type IN ('sale','production_consume') 
                    THEN -CAST(quantity AS REAL)
                    ELSE 0
                END
            ) as total_qty
            FROM inventory_movements
            WHERE item_id = ?
        ''', (item_id,))
        row = cur.fetchone()
        new_qty = Decimal(str(row[0])) if row[0] else Decimal('0')
        conn.execute("UPDATE items SET quantity = ? WHERE id = ?", (str(new_qty), item_id))
        conn.commit()

    def _recalculate_average_cost(self, item_id):
        conn = self.get_connection()
        cur = conn.execute('''
            SELECT 
                SUM(CAST(quantity AS REAL)) as total_qty,
                SUM(CAST(quantity AS REAL) * CAST(unit_cost AS REAL)) as total_cost
            FROM inventory_movements
            WHERE item_id = ? AND movement_type IN ('opening', 'purchase', 'adjustment', 'production_out', 'sales_return')
        ''', (item_id,))
        row = cur.fetchone()
        total_qty = Decimal(str(row[0])) if row[0] else Decimal('0')
        total_cost = Decimal(str(row[1])) if row[1] else Decimal('0')
        avg = total_cost / total_qty if total_qty > 0 else Decimal('0')
        conn.execute("UPDATE items SET average_cost = ? WHERE id = ?", (str(avg), item_id))
        conn.commit()

    def _update_cash_balance(self, amount, add=True):
        from auth.session import UserSession
        uid = UserSession.get_current_user_id()
        sign = 1 if add else -1
        conn = self.get_connection()
        conn.execute("UPDATE users SET cash_balance = CAST(COALESCE(cash_balance, '0') AS TEXT) + ? WHERE id=?",
                     (str(sign * amount), uid))
        conn.commit()

    def _update_customer_balance(self, customer_id, delta):
        conn = self.get_connection()
        conn.execute("UPDATE customers SET balance = CAST(COALESCE(balance, '0') AS TEXT) + ? WHERE id=?",
                     (str(delta), customer_id))
        conn.commit()

    def _update_supplier_balance(self, supplier_id, delta):
        conn = self.get_connection()
        conn.execute("UPDATE suppliers SET balance = CAST(COALESCE(balance, '0') AS TEXT) + ? WHERE id=?",
                     (str(delta), supplier_id))
        conn.commit()

    def _update_invoice_paid(self, invoice_id, amount, add=True):
        conn = self.get_connection()
        if add:
            conn.execute("UPDATE invoices SET paid = CAST(paid AS REAL) + ? WHERE id=?", (str(amount), invoice_id))
        else:
            conn.execute("UPDATE invoices SET paid = CAST(paid AS REAL) - ? WHERE id=?", (str(amount), invoice_id))
        conn.execute("UPDATE invoices SET paid = MAX(paid, 0) WHERE id=?", (invoice_id,))
        conn.commit()

    # ------------------- دوال الإعدادات وأسعار الصرف -------------------
    def get_setting(self, key: str, default=None):
        if self.is_remote():
            if self._rest_client is None or self._rest_client.token is None:
                return default
            val = self._rest_client.get_setting(key)
            return val if val is not None else default
        conn = self.get_connection()
        row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return row['value'] if row else default

    def set_setting(self, key: str, value: str):
        if self.is_remote():
            self._rest_client.set_setting(key, value)
            return
        conn = self.get_connection()
        conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
        conn.commit()

    def get_all_currencies(self):
        if self.is_remote():
            if self._rest_client is None or self._rest_client.token is None:
                return []
            return self._rest_client.get_all_currencies()
        conn = self.get_connection()
        rows = conn.execute("SELECT currency_code, rate_to_usd, updated_at FROM exchange_rates ORDER BY currency_code").fetchall()
        return [dict(row) for row in rows]

    def update_exchange_rate(self, currency_code: str, rate_to_usd: float):
        if self.is_remote():
            self._rest_client.update_exchange_rate(currency_code, rate_to_usd)
            return
        conn = self.get_connection()
        now = datetime.datetime.now().isoformat()
        conn.execute("INSERT OR REPLACE INTO exchange_rates (currency_code, rate_to_usd, updated_at) VALUES (?, ?, ?)",
                     (currency_code, rate_to_usd, now))
        conn.commit()

DB_PATH = LOCAL_DB_PATH


