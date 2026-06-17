# -*- coding: utf-8 -*-
import sqlite3
import os
import datetime
from alrajhi_server.auth.password import hash_password
from .schema_manager import apply_common_schema
from .paths import get_server_db_path

DB_PATH = get_server_db_path()

def init_database():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys=ON')
    cursor = conn.cursor()

    # جداول الراجحي الأساسية (مطابقة للعميل)
    cursor.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            full_name TEXT,
            role TEXT DEFAULT 'user',
            branch_id INTEGER,
            created_at TEXT,
            last_login TEXT,
            cash_balance TEXT DEFAULT '0',
            force_password_change INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            name TEXT NOT NULL,
            phone TEXT,
            address TEXT,
            balance TEXT DEFAULT '0',
            FOREIGN KEY (user_id) REFERENCES users(id),
            UNIQUE(user_id, name)
        );

        CREATE TABLE IF NOT EXISTS suppliers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            name TEXT NOT NULL,
            phone TEXT,
            address TEXT,
            balance TEXT DEFAULT '0',
            FOREIGN KEY (user_id) REFERENCES users(id),
            UNIQUE(user_id, name)
        );

        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            name TEXT NOT NULL,
            parent_id INTEGER,
            description TEXT,
            color TEXT DEFAULT '#64748B',
            icon TEXT DEFAULT 'folder',
            is_active INTEGER DEFAULT 1,
            deleted_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (parent_id) REFERENCES categories(id),
            UNIQUE(user_id, name, parent_id)
        );

        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            name TEXT NOT NULL,
            category_id INTEGER,
            item_type TEXT,
            purchase_price TEXT DEFAULT '0',
            selling_price TEXT DEFAULT '0',
            quantity TEXT DEFAULT '0',
            unit TEXT,
            average_cost TEXT DEFAULT '0',
            barcode TEXT,
            reorder_level TEXT DEFAULT '0',
            deleted_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id),
            UNIQUE(user_id, name)
        );

        CREATE TABLE IF NOT EXISTS item_units (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id INTEGER,
            unit_name TEXT NOT NULL,
            conversion_factor TEXT DEFAULT '1',
            FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            type TEXT,
            customer_id INTEGER,
            supplier_id INTEGER,
            date TEXT,
            due_date TEXT,
            reference TEXT,
            notes TEXT,
            total TEXT DEFAULT '0',
            paid TEXT DEFAULT '0',
            status TEXT,
            workflow_status TEXT DEFAULT 'DRAFT',
            submitted_at TEXT,
            submitted_by TEXT,
            approved_at TEXT,
            approved_by TEXT,
            posted_at TEXT,
            posted_by TEXT,
            cancelled_at TEXT,
            cancelled_by TEXT,
            deleted_at TEXT,
            deleted_by TEXT,
            exchange_rate_to_usd REAL DEFAULT 1.0,
            original_currency TEXT DEFAULT 'USD',
            warehouse_id INTEGER,
            branch_id INTEGER,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (customer_id) REFERENCES customers(id),
            FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
        );

        CREATE TABLE IF NOT EXISTS invoice_lines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_id INTEGER,
            item_id INTEGER,
            description TEXT,
            quantity TEXT DEFAULT '0',
            unit_price TEXT DEFAULT '0',
            total TEXT DEFAULT '0',
            unit TEXT,
            quantity_in_base TEXT DEFAULT '0',
            unit_cost TEXT DEFAULT '0',
            cost_amount TEXT DEFAULT '0',
            production_order_id INTEGER,
            FOREIGN KEY (invoice_id) REFERENCES invoices(id) ON DELETE CASCADE,
            FOREIGN KEY (item_id) REFERENCES items(id)
        );

        CREATE TABLE IF NOT EXISTS vouchers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            type TEXT,
            date TEXT,
            amount TEXT DEFAULT '0',
            description TEXT,
            reference TEXT,
            customer_id INTEGER,
            supplier_id INTEGER,
            invoice_id INTEGER,
            exchange_rate_to_usd REAL DEFAULT 1.0,
            original_currency TEXT DEFAULT 'USD',
            warehouse_id INTEGER,
            branch_id INTEGER,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (customer_id) REFERENCES customers(id),
            FOREIGN KEY (supplier_id) REFERENCES suppliers(id),
            FOREIGN KEY (invoice_id) REFERENCES invoices(id)
        );

        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            amount TEXT DEFAULT '0',
            expense_date TEXT,
            description TEXT,
            exchange_rate_to_usd REAL DEFAULT 1.0,
            original_currency TEXT DEFAULT 'USD',
            warehouse_id INTEGER,
            branch_id INTEGER,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );



        
        CREATE TABLE IF NOT EXISTS branches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            name TEXT NOT NULL,
            code TEXT,
            address TEXT,
            phone TEXT,
            notes TEXT,
            branch_id INTEGER,
            is_default INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            deleted_at TEXT,
            created_at TEXT,
            updated_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id),
            UNIQUE(user_id, name),
            UNIQUE(user_id, code)
        );

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

        CREATE TABLE IF NOT EXISTS inventory_movements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id INTEGER NOT NULL,
            user_id TEXT NOT NULL,
            movement_type TEXT NOT NULL,
            quantity TEXT NOT NULL,
            unit_cost TEXT,
            reference_id INTEGER,
            movement_date TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (item_id) REFERENCES items(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        );



        CREATE TABLE IF NOT EXISTS inventory_ledger (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            item_id INTEGER NOT NULL,
            warehouse_id INTEGER,
            movement_type TEXT NOT NULL,
            direction TEXT NOT NULL CHECK(direction IN ('in','out','neutral')),
            quantity TEXT NOT NULL,
            unit_cost TEXT,
            total_cost TEXT,
            reference_type TEXT,
            reference_id INTEGER,
            source_table TEXT,
            source_id INTEGER,
            notes TEXT,
            movement_date TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (item_id) REFERENCES items(id),
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (warehouse_id) REFERENCES warehouses(id)
        );

        CREATE TABLE IF NOT EXISTS bom (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            quantity TEXT DEFAULT '1',
            user_id TEXT NOT NULL,
            created_at TEXT,
            updated_at TEXT,
            FOREIGN KEY (product_id) REFERENCES items(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS bom_lines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bom_id INTEGER NOT NULL,
            item_id INTEGER NOT NULL,
            quantity TEXT NOT NULL,
            unit_id INTEGER,
            waste_percent TEXT DEFAULT '0',
            FOREIGN KEY (bom_id) REFERENCES bom(id) ON DELETE CASCADE,
            FOREIGN KEY (item_id) REFERENCES items(id)
        );

        CREATE TABLE IF NOT EXISTS bom_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_number TEXT NOT NULL,
            product_id INTEGER NOT NULL,
            product_name TEXT,
            created_at TEXT,
            FOREIGN KEY (product_id) REFERENCES items(id)
        );

        CREATE TABLE IF NOT EXISTS bom_snapshot_lines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            snapshot_id INTEGER NOT NULL,
            item_id INTEGER NOT NULL,
            item_name TEXT,
            quantity TEXT NOT NULL,
            unit_name TEXT,
            conversion_factor TEXT DEFAULT '1',
            waste_percent TEXT DEFAULT '0',
            FOREIGN KEY (snapshot_id) REFERENCES bom_snapshots(id) ON DELETE CASCADE,
            FOREIGN KEY (item_id) REFERENCES items(id)
        );

        CREATE TABLE IF NOT EXISTS production_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_number TEXT UNIQUE NOT NULL,
            product_id INTEGER NOT NULL,
            planned_qty TEXT NOT NULL,
            produced_qty TEXT DEFAULT '0',
            status TEXT DEFAULT 'planned',
            start_date TEXT,
            end_date TEXT,
            user_id TEXT NOT NULL,
            created_at TEXT,
            notes TEXT,
            bom_snapshot_id INTEGER,
            raw_warehouse_id INTEGER,
            output_warehouse_id INTEGER,
            FOREIGN KEY (product_id) REFERENCES items(id),
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (bom_snapshot_id) REFERENCES bom_snapshots(id)
        );

        CREATE TABLE IF NOT EXISTS production_consumptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            item_id INTEGER NOT NULL,
            consumed_qty TEXT NOT NULL,
            unit_cost TEXT,
            movement_date TEXT NOT NULL,
            FOREIGN KEY (order_id) REFERENCES production_orders(id),
            FOREIGN KEY (item_id) REFERENCES items(id)
        );

        CREATE TABLE IF NOT EXISTS production_outputs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            item_id INTEGER NOT NULL,
            produced_qty TEXT NOT NULL,
            unit_cost TEXT,
            output_date TEXT NOT NULL,
            FOREIGN KEY (order_id) REFERENCES production_orders(id),
            FOREIGN KEY (item_id) REFERENCES items(id)
        );

        CREATE TABLE IF NOT EXISTS exchange_rates (
            currency_code TEXT PRIMARY KEY,
            rate_to_usd REAL NOT NULL,
            updated_at TEXT
        );

        CREATE TABLE IF NOT EXISTS exchange_rate_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            currency_code TEXT NOT NULL,
            rate_to_usd REAL NOT NULL,
            effective_date TEXT NOT NULL,
            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT,
            category TEXT,
            updated_at TEXT
        );

        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            username TEXT,
            action TEXT,
            table_name TEXT,
            record_id INTEGER,
            details TEXT,
            ip_address TEXT,
            timestamp TEXT,
            event_time TEXT,
            entity_type TEXT,
            entity_id INTEGER,
            old_values TEXT,
            new_values TEXT,
            session_id TEXT,
            source TEXT
        );

        CREATE TABLE IF NOT EXISTS token_blacklist (
            jti TEXT PRIMARY KEY,
            created_at TEXT
        );
    ''')

    # ترقيات آمنة للجداول القديمة
    cursor.execute("PRAGMA table_info(items)")
    item_columns = [row[1] for row in cursor.fetchall()]
    if 'deleted_at' not in item_columns:
        cursor.execute("ALTER TABLE items ADD COLUMN deleted_at TEXT")
    if 'reorder_level' not in item_columns:
        cursor.execute("ALTER TABLE items ADD COLUMN reorder_level TEXT DEFAULT '0'")

    
    # Phase151 workflow lifecycle columns for server databases
    cursor.execute("PRAGMA table_info(invoices)")
    invoice_columns = {row[1] for row in cursor.fetchall()}
    for col_name, col_type in [
        ('due_date', 'TEXT'),
        ('workflow_status', "TEXT DEFAULT 'DRAFT'"),
        ('submitted_at', 'TEXT'),
        ('submitted_by', 'TEXT'),
        ('approved_at', 'TEXT'),
        ('approved_by', 'TEXT'),
        ('posted_at', 'TEXT'),
        ('posted_by', 'TEXT'),
        ('cancelled_at', 'TEXT'),
        ('cancelled_by', 'TEXT'),
        ('deleted_by', 'TEXT'),
    ]:
        if col_name not in invoice_columns:
            cursor.execute(f"ALTER TABLE invoices ADD COLUMN {col_name} {col_type}")
            invoice_columns.add(col_name)
    cursor.executescript('''
        CREATE TABLE IF NOT EXISTS workflow_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entity_type TEXT NOT NULL,
            entity_id INTEGER NOT NULL,
            old_status TEXT,
            new_status TEXT NOT NULL,
            action TEXT NOT NULL,
            username TEXT,
            user_id TEXT,
            notes TEXT,
            created_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_workflow_events_entity ON workflow_events(entity_type, entity_id, created_at);
        -- idx_invoices_workflow_status is created after safe ALTER migrations.
    ''')
    # server-safe workflow index guard: create only after ALTER TABLE has ensured the column exists.
    cursor.execute("PRAGMA table_info(invoices)")
    _invoice_cols_for_workflow_index = {row[1] for row in cursor.fetchall()}
    if 'workflow_status' in _invoice_cols_for_workflow_index:
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_invoices_workflow_status ON invoices(workflow_status)")


    cursor.execute("PRAGMA table_info(settings)")
    settings_columns = [row[1] for row in cursor.fetchall()]
    if 'category' not in settings_columns:
        cursor.execute("ALTER TABLE settings ADD COLUMN category TEXT")
    if 'updated_at' not in settings_columns:
        cursor.execute("ALTER TABLE settings ADD COLUMN updated_at TEXT")

    # Production-readiness: normalize legacy columns before indexes/default data.
    apply_common_schema(conn)

    # فهارس
    for _idx_sql in [
        'CREATE INDEX IF NOT EXISTS idx_wh_user ON warehouses(user_id);',
        'CREATE INDEX IF NOT EXISTS idx_wh_bal_item ON item_warehouse_balances(item_id);',
        'CREATE INDEX IF NOT EXISTS idx_wh_bal_wh ON item_warehouse_balances(warehouse_id);',
        'CREATE INDEX IF NOT EXISTS idx_wh_mov_item ON warehouse_movements(item_id);',
        'CREATE INDEX IF NOT EXISTS idx_wh_mov_wh ON warehouse_movements(warehouse_id);',
        'CREATE INDEX IF NOT EXISTS idx_items_barcode ON items(barcode) WHERE barcode IS NOT NULL;',
        'CREATE INDEX IF NOT EXISTS idx_invoices_user_id ON invoices(user_id);',
        'CREATE INDEX IF NOT EXISTS idx_invoices_date ON invoices(date);',
        'CREATE INDEX IF NOT EXISTS idx_inventory_ledger_user_item ON inventory_ledger(user_id, item_id);',
        'CREATE INDEX IF NOT EXISTS idx_inventory_ledger_item_date ON inventory_ledger(item_id, movement_date);',
        'CREATE INDEX IF NOT EXISTS idx_inventory_ledger_ref ON inventory_ledger(reference_type, reference_id);',
        'CREATE INDEX IF NOT EXISTS idx_production_orders_product_id ON production_orders(product_id);',
        'CREATE INDEX IF NOT EXISTS idx_bom_product_id ON bom(product_id);',
        'CREATE INDEX IF NOT EXISTS idx_audit_log_user ON audit_log(user_id);',
        'CREATE INDEX IF NOT EXISTS idx_audit_log_timestamp ON audit_log(timestamp);',
        'CREATE INDEX IF NOT EXISTS idx_audit_log_entity ON audit_log(entity_type, entity_id);',
        'CREATE INDEX IF NOT EXISTS idx_audit_log_action ON audit_log(action);',
        'CREATE INDEX IF NOT EXISTS idx_exch_rate_hist_currency_date ON exchange_rate_history(currency_code, effective_date);'
    ]:
        try:
            cursor.execute(_idx_sql)
        except sqlite3.OperationalError as exc:
            # Production-readiness hotfix: old databases may have legacy tables
            # without newer indexed columns. Index creation must never block
            # schema upgrade; later migrations add/normalize missing columns.
            msg = str(exc).lower()
            if 'no such column' in msg or 'no such table' in msg:
                continue
            raise

    # إعدادات افتراضية
    cursor.executescript('''
        INSERT OR IGNORE INTO settings (key, value) VALUES ('currency_decimals', '2');
        INSERT OR IGNORE INTO settings (key, value) VALUES ('number_format', 'western');
        INSERT OR IGNORE INTO settings (key, value) VALUES ('language', 'ar');
        INSERT OR IGNORE INTO settings (key, value) VALUES ('theme', 'light');
        INSERT OR IGNORE INTO settings (key, value) VALUES ('base_currency', 'USD');
        INSERT OR IGNORE INTO settings (key, value) VALUES ('display_currency', 'SYP');
        INSERT OR IGNORE INTO settings (key, value) VALUES ('abbreviate_numbers', 'false');

        INSERT OR IGNORE INTO settings (key, value, category) VALUES ('invoice/sales_prefix', 'SAL-', 'invoices');
        INSERT OR IGNORE INTO settings (key, value, category) VALUES ('invoice/purchase_prefix', 'PUR-', 'invoices');
        INSERT OR IGNORE INTO settings (key, value, category) VALUES ('invoice/auto_numbering', 'true', 'invoices');
        INSERT OR IGNORE INTO settings (key, value, category) VALUES ('invoice/show_profit', 'false', 'invoices');
        INSERT OR IGNORE INTO settings (key, value, category) VALUES ('invoice/show_cost', 'false', 'invoices');
        INSERT OR IGNORE INTO settings (key, value, category) VALUES ('inventory/allow_negative_stock', 'false', 'inventory');
        INSERT OR IGNORE INTO settings (key, value, category) VALUES ('inventory/default_reorder_level', '0', 'inventory');
        INSERT OR IGNORE INTO settings (key, value, category) VALUES ('inventory/cost_method', 'AVERAGE', 'inventory');
        INSERT OR IGNORE INTO settings (key, value, category) VALUES ('units/default_sale_unit', 'قطعة', 'units');
        INSERT OR IGNORE INTO settings (key, value, category) VALUES ('units/default_purchase_unit', 'قطعة', 'units');
        INSERT OR IGNORE INTO settings (key, value, category) VALUES ('returns/max_days', '30', 'returns');
        INSERT OR IGNORE INTO settings (key, value, category) VALUES ('manufacturing/cost_method', 'MATERIALS_ONLY', 'manufacturing');
        INSERT OR IGNORE INTO settings (key, value, category) VALUES ('reports/default_limit', '100', 'reports');
        INSERT OR IGNORE INTO settings (key, value, category) VALUES ('workflow/enabled', 'false', 'workflow');
        INSERT OR IGNORE INTO settings (key, value, category) VALUES ('workflow/approval_required', 'false', 'workflow');
        INSERT OR IGNORE INTO settings (key, value, category) VALUES ('workflow/sales_approval_threshold', '0', 'workflow');
        INSERT OR IGNORE INTO settings (key, value, category) VALUES ('workflow/purchase_approval_threshold', '0', 'workflow');
        INSERT OR IGNORE INTO settings (key, value, category) VALUES ('workflow/allow_edit_draft', 'true', 'workflow');
        INSERT OR IGNORE INTO settings (key, value, category) VALUES ('workflow/allow_edit_submitted', 'true', 'workflow');
        INSERT OR IGNORE INTO settings (key, value, category) VALUES ('workflow/allow_edit_approved', 'false', 'workflow');
        INSERT OR IGNORE INTO settings (key, value, category) VALUES ('workflow/allow_edit_posted', 'false', 'workflow');
        INSERT OR IGNORE INTO settings (key, value, category) VALUES ('workflow/allow_edit_cancelled', 'false', 'workflow');
        INSERT OR IGNORE INTO settings (key, value, category) VALUES ('workflow/allow_delete_draft', 'true', 'workflow');
        INSERT OR IGNORE INTO settings (key, value, category) VALUES ('workflow/allow_delete_submitted', 'true', 'workflow');
        INSERT OR IGNORE INTO settings (key, value, category) VALUES ('workflow/allow_delete_approved', 'false', 'workflow');
        INSERT OR IGNORE INTO settings (key, value, category) VALUES ('workflow/allow_delete_posted', 'false', 'workflow');
        INSERT OR IGNORE INTO settings (key, value, category) VALUES ('workflow/allow_delete_cancelled', 'false', 'workflow');
    ''')

    # مستخدم admin افتراضي
    cursor.execute("SELECT id FROM users WHERE username = 'admin'")
    if not cursor.fetchone():
        admin_password = os.environ.get('ALRAJHI_ADMIN_PASSWORD', 'admin123')
        if (os.environ.get('ALRAJHI_ENV') == 'production' or os.environ.get('FLASK_ENV') == 'production') and admin_password == 'admin123':
            raise RuntimeError('ALRAJHI_ADMIN_PASSWORD must be set in production')
        pwd_hash, salt = hash_password(admin_password)
        now = datetime.datetime.now().isoformat()
        cursor.execute('''
            INSERT INTO users (id, username, password_hash, salt, full_name, role, created_at, cash_balance, force_password_change)
            VALUES (?,?,?,?,?,?,?,?,?)
        ''', ('admin', 'admin', pwd_hash, salt, 'المدير العام', 'admin', now, '0', 1))

    # أسعار صرف افتراضية
    now = datetime.datetime.now().isoformat()
    default_rates = [
        ('USD', 1.0), ('SAR', 3.75), ('SYP', 14000.0), ('EUR', 0.92),
        ('GBP', 0.79), ('AED', 3.67), ('QAR', 3.64), ('KWD', 0.31), ('OMR', 0.38),
    ]
    for code, rate in default_rates:
        cursor.execute("INSERT OR IGNORE INTO exchange_rates (currency_code, rate_to_usd, updated_at) VALUES (?,?,?)",
                       (code, rate, now))

    
    # Branches core migration/bootstrap

    # Branch operational integration columns
    for table, coldef in [
        ('users', 'branch_id INTEGER'),
        ('invoices', 'branch_id INTEGER'),
        ('vouchers', 'branch_id INTEGER'),
        ('expenses', 'branch_id INTEGER')
    ]:
        try:
            cursor.execute(f"PRAGMA table_info({table})")
            _cols = {row[1] for row in cursor.fetchall()}
            cname = coldef.split()[0]
            if cname not in _cols:
                cursor.execute(f"ALTER TABLE {table} ADD COLUMN {coldef}")
        except Exception:
            pass
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_branch ON users(branch_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_invoices_branch ON invoices(branch_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_vouchers_branch ON vouchers(branch_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_expenses_branch ON expenses(branch_id)")

    try:
        cursor.execute("ALTER TABLE warehouses ADD COLUMN branch_id INTEGER")
    except Exception:
        pass
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_branches_user ON branches(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_warehouses_branch ON warehouses(branch_id)")
    now = datetime.datetime.now().isoformat()
    users_for_branches = cursor.execute('''
        SELECT id FROM users
        UNION
        SELECT DISTINCT user_id AS id FROM warehouses WHERE user_id IS NOT NULL
        UNION
        SELECT DISTINCT user_id AS id FROM items WHERE user_id IS NOT NULL
    ''').fetchall()
    for user_row in users_for_branches:
        uid = user_row['id'] if hasattr(user_row, 'keys') else user_row[0]
        if not uid:
            continue
        branch = cursor.execute(
            "SELECT id FROM branches WHERE user_id=? AND is_default=1 AND deleted_at IS NULL LIMIT 1",
            (uid,)
        ).fetchone()
        if branch:
            branch_id = branch['id'] if hasattr(branch, 'keys') else branch[0]
        else:
            cursor.execute('''
                INSERT OR IGNORE INTO branches
                (user_id, name, code, address, phone, notes, is_default, is_active, created_at, updated_at)
                VALUES (?, 'الفرع الرئيسي', 'MAIN', '', '', 'تم إنشاؤه تلقائياً عند تفعيل نظام الفروع', 1, 1, ?, ?)
            ''', (uid, now, now))
            branch = cursor.execute("SELECT id FROM branches WHERE user_id=? AND is_default=1 LIMIT 1", (uid,)).fetchone()
            branch_id = branch['id'] if hasattr(branch, 'keys') else branch[0]
        cursor.execute("UPDATE warehouses SET branch_id=? WHERE user_id=? AND branch_id IS NULL", (branch_id, uid))
        cursor.execute("UPDATE users SET branch_id=? WHERE id=? AND branch_id IS NULL", (branch_id, uid))
        cursor.execute("UPDATE invoices SET branch_id=? WHERE user_id=? AND branch_id IS NULL", (branch_id, uid))
        cursor.execute("UPDATE vouchers SET branch_id=? WHERE user_id=? AND branch_id IS NULL", (branch_id, uid))
        try:
            cursor.execute("UPDATE expenses SET branch_id=? WHERE user_id=? AND branch_id IS NULL", (branch_id, uid))
        except Exception:
            pass


    # System-3.1 Sales Returns Management
    cursor.executescript('''
        CREATE TABLE IF NOT EXISTS sales_returns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            return_no TEXT,
            original_invoice_id INTEGER NOT NULL,
            customer_id INTEGER,
            date TEXT,
            total TEXT DEFAULT '0',
            refund_amount TEXT DEFAULT '0',
            credit_amount TEXT DEFAULT '0',
            warehouse_id INTEGER,
            branch_id INTEGER,
            cashbox_id INTEGER,
            bank_account_id INTEGER,
            payment_method TEXT DEFAULT 'cash',
            notes TEXT,
            status TEXT DEFAULT 'active',
            deleted_at TEXT,
            created_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (original_invoice_id) REFERENCES invoices(id),
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        );
        CREATE TABLE IF NOT EXISTS sales_return_lines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sales_return_id INTEGER NOT NULL,
            original_invoice_line_id INTEGER,
            item_id INTEGER NOT NULL,
            quantity TEXT DEFAULT '0',
            unit_price TEXT DEFAULT '0',
            total TEXT DEFAULT '0',
            unit TEXT,
            quantity_in_base TEXT DEFAULT '0',
            unit_cost TEXT DEFAULT '0',
            cost_amount TEXT DEFAULT '0',
            FOREIGN KEY (sales_return_id) REFERENCES sales_returns(id) ON DELETE CASCADE,
            FOREIGN KEY (item_id) REFERENCES items(id)
        );
        CREATE INDEX IF NOT EXISTS idx_sales_returns_user ON sales_returns(user_id);
        CREATE INDEX IF NOT EXISTS idx_sales_returns_invoice ON sales_returns(original_invoice_id);
        CREATE INDEX IF NOT EXISTS idx_sales_returns_branch ON sales_returns(branch_id);
        CREATE INDEX IF NOT EXISTS idx_sales_return_lines_return ON sales_return_lines(sales_return_id);

    ''')

    cursor.executescript('''
        CREATE TABLE IF NOT EXISTS purchase_returns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            return_no TEXT,
            original_invoice_id INTEGER NOT NULL,
            supplier_id INTEGER,
            date TEXT NOT NULL,
            total TEXT NOT NULL DEFAULT '0',
            refund_amount TEXT NOT NULL DEFAULT '0',
            credit_amount TEXT NOT NULL DEFAULT '0',
            warehouse_id INTEGER,
            branch_id INTEGER,
            cashbox_id INTEGER,
            bank_account_id INTEGER,
            payment_method TEXT DEFAULT 'cash',
            notes TEXT,
            status TEXT DEFAULT 'active',
            created_at TEXT,
            deleted_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (original_invoice_id) REFERENCES invoices(id),
            FOREIGN KEY (supplier_id) REFERENCES suppliers(id),
            FOREIGN KEY (warehouse_id) REFERENCES warehouses(id),
            FOREIGN KEY (branch_id) REFERENCES branches(id)
        );
        CREATE TABLE IF NOT EXISTS purchase_return_lines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            purchase_return_id INTEGER NOT NULL,
            original_invoice_line_id INTEGER,
            item_id INTEGER NOT NULL,
            quantity TEXT NOT NULL,
            unit_price TEXT NOT NULL DEFAULT '0',
            total TEXT NOT NULL DEFAULT '0',
            unit TEXT,
            quantity_in_base TEXT NOT NULL DEFAULT '0',
            unit_cost TEXT NOT NULL DEFAULT '0',
            cost_amount TEXT NOT NULL DEFAULT '0',
            FOREIGN KEY (purchase_return_id) REFERENCES purchase_returns(id) ON DELETE CASCADE,
            FOREIGN KEY (item_id) REFERENCES items(id)
        );
        CREATE INDEX IF NOT EXISTS idx_purchase_returns_user ON purchase_returns(user_id);
        CREATE INDEX IF NOT EXISTS idx_purchase_returns_invoice ON purchase_returns(original_invoice_id);
        CREATE INDEX IF NOT EXISTS idx_purchase_returns_branch ON purchase_returns(branch_id);
        CREATE INDEX IF NOT EXISTS idx_purchase_return_lines_return ON purchase_return_lines(purchase_return_id);
    ''')

    apply_common_schema(conn)

    # Phase152/153 approval + accounting foundation tables
    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS approval_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entity_type TEXT NOT NULL,
            entity_id INTEGER NOT NULL,
            amount TEXT DEFAULT '0',
            threshold_amount TEXT DEFAULT '0',
            status TEXT NOT NULL DEFAULT 'PENDING',
            requested_by TEXT,
            requested_at TEXT,
            decided_by TEXT,
            decided_at TEXT,
            decision_notes TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT,
            UNIQUE(entity_type, entity_id)
        );
        CREATE INDEX IF NOT EXISTS idx_approval_requests_status ON approval_requests(status, entity_type);
        CREATE TABLE IF NOT EXISTS accounts (id INTEGER PRIMARY KEY AUTOINCREMENT, code TEXT UNIQUE NOT NULL, name TEXT NOT NULL, type TEXT NOT NULL, parent_id INTEGER, is_active INTEGER DEFAULT 1, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS journal_entries (id INTEGER PRIMARY KEY AUTOINCREMENT, entry_no TEXT UNIQUE, entry_date TEXT NOT NULL, source_type TEXT, source_id INTEGER, description TEXT, status TEXT DEFAULT 'POSTED', created_by TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP, UNIQUE(source_type, source_id));
        CREATE TABLE IF NOT EXISTS journal_lines (id INTEGER PRIMARY KEY AUTOINCREMENT, journal_entry_id INTEGER NOT NULL, account_id INTEGER NOT NULL, debit TEXT DEFAULT '0', credit TEXT DEFAULT '0', memo TEXT, FOREIGN KEY(journal_entry_id) REFERENCES journal_entries(id) ON DELETE CASCADE, FOREIGN KEY(account_id) REFERENCES accounts(id));
        CREATE INDEX IF NOT EXISTS idx_journal_entries_source ON journal_entries(source_type, source_id);
        INSERT OR IGNORE INTO accounts(code, name, type) VALUES ('1000','Cash / صندوق','ASSET');
        INSERT OR IGNORE INTO accounts(code, name, type) VALUES ('1100','Accounts Receivable / ذمم العملاء','ASSET');
        INSERT OR IGNORE INTO accounts(code, name, type) VALUES ('1200','Inventory / مخزون','ASSET');
        INSERT OR IGNORE INTO accounts(code, name, type) VALUES ('2000','Accounts Payable / ذمم الموردين','LIABILITY');
        INSERT OR IGNORE INTO accounts(code, name, type) VALUES ('3000','Owner Equity / حقوق الملكية','EQUITY');
        INSERT OR IGNORE INTO accounts(code, name, type) VALUES ('3100','Retained Earnings / أرباح مرحلة','EQUITY');
        INSERT OR IGNORE INTO accounts(code, name, type) VALUES ('3900','Current Year Earnings / أرباح السنة الحالية','EQUITY');
        INSERT OR IGNORE INTO accounts(code, name, type) VALUES ('4000','Sales Revenue / إيرادات المبيعات','REVENUE');
        INSERT OR IGNORE INTO accounts(code, name, type) VALUES ('5000','Purchases / مشتريات','EXPENSE');
        INSERT OR IGNORE INTO accounts(code, name, type) VALUES ('5900','Closing Summary / ملخص الإقفال','EQUITY');
        CREATE TABLE IF NOT EXISTS accounting_periods (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, start_date TEXT NOT NULL, end_date TEXT NOT NULL, status TEXT DEFAULT 'OPEN', closed_at TEXT, closed_by TEXT, closing_entry_id INTEGER, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE INDEX IF NOT EXISTS idx_accounting_periods_dates ON accounting_periods(start_date, end_date, status);
        INSERT OR IGNORE INTO settings (key, value, category) VALUES ('approval/non_admin_can_approve', 'false', 'approval');
    """)

    # Phase157: Enterprise RBAC tables and default policies

    # Phase158/159 hardening: old databases may already have shallow RBAC tables.
    def _table_exists_local(name):
        cursor.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND lower(name)=lower(?) LIMIT 1", (name,))
        return cursor.fetchone() is not None
    def _columns_local(name):
        if not _table_exists_local(name):
            return set()
        cursor.execute(f"PRAGMA table_info({name})")
        return {row[1] for row in cursor.fetchall()}
    def _add_col_local(table, col, ddl):
        if _table_exists_local(table) and col not in _columns_local(table):
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col} {ddl}")
    _add_col_local('roles','display_name','TEXT')
    _add_col_local('roles','description','TEXT')
    _add_col_local('roles','is_system','INTEGER DEFAULT 0')
    _add_col_local('roles','is_active','INTEGER DEFAULT 1')
    _add_col_local('roles','created_at','TEXT DEFAULT CURRENT_TIMESTAMP')
    _add_col_local('permissions','module','TEXT')
    _add_col_local('permissions','action','TEXT')
    _add_col_local('permissions','description','TEXT')
    _add_col_local('permissions','created_at','TEXT DEFAULT CURRENT_TIMESTAMP')

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS roles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            display_name TEXT,
            description TEXT,
            is_system INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS permissions (
            key TEXT PRIMARY KEY,
            module TEXT NOT NULL,
            action TEXT NOT NULL,
            description TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS role_permissions (
            role_id INTEGER NOT NULL,
            permission_key TEXT NOT NULL,
            allowed INTEGER NOT NULL DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY(role_id, permission_key),
            FOREIGN KEY(role_id) REFERENCES roles(id) ON DELETE CASCADE,
            FOREIGN KEY(permission_key) REFERENCES permissions(key) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS user_roles (
            user_id TEXT NOT NULL,
            role_id INTEGER NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY(user_id, role_id),
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY(role_id) REFERENCES roles(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS user_branch_access (
            user_id TEXT NOT NULL,
            branch_id INTEGER NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY(user_id, branch_id),
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY(branch_id) REFERENCES branches(id) ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS idx_user_roles_user ON user_roles(user_id);
        CREATE INDEX IF NOT EXISTS idx_role_permissions_role ON role_permissions(role_id);
        CREATE INDEX IF NOT EXISTS idx_user_branch_access_user ON user_branch_access(user_id);

        INSERT OR IGNORE INTO roles(name, display_name, description, is_system) VALUES ('admin','Administrator / مدير النظام','Full system access',1);
        INSERT OR IGNORE INTO roles(name, display_name, description, is_system) VALUES ('manager','Manager / مدير','Operational management access',1);
        INSERT OR IGNORE INTO roles(name, display_name, description, is_system) VALUES ('accountant','Accountant / محاسب','Accounting and financial reporting access',1);
        INSERT OR IGNORE INTO roles(name, display_name, description, is_system) VALUES ('cashier','Cashier / أمين صندوق','Sales and cashbox access',1);
        INSERT OR IGNORE INTO roles(name, display_name, description, is_system) VALUES ('viewer','Viewer / مشاهدة','Read-only access',1);

        INSERT OR IGNORE INTO permissions(key,module,action,description) VALUES ('reports.view','reports','view','View reports');
        INSERT OR IGNORE INTO permissions(key,module,action,description) VALUES ('reports.export','reports','export','Export reports');
        INSERT OR IGNORE INTO permissions(key,module,action,description) VALUES ('invoices.edit','invoices','edit','Edit invoices');
        INSERT OR IGNORE INTO permissions(key,module,action,description) VALUES ('invoices.delete','invoices','delete','Delete invoices');
        INSERT OR IGNORE INTO permissions(key,module,action,description) VALUES ('returns.edit','returns','edit','Edit returns');
        INSERT OR IGNORE INTO permissions(key,module,action,description) VALUES ('branches.view_all','branches','view_all','View all branches');
        INSERT OR IGNORE INTO permissions(key,module,action,description) VALUES ('branches.manage_all','branches','manage_all','Manage all branches');
        INSERT OR IGNORE INTO permissions(key,module,action,description) VALUES ('approval.submit','approval','submit','Submit documents for approval');
        INSERT OR IGNORE INTO permissions(key,module,action,description) VALUES ('approval.approve','approval','approve','Approve documents');
        INSERT OR IGNORE INTO permissions(key,module,action,description) VALUES ('approval.reject','approval','reject','Reject approval requests');
        INSERT OR IGNORE INTO permissions(key,module,action,description) VALUES ('accounting.view','accounting','view','View accounting reports');
        INSERT OR IGNORE INTO permissions(key,module,action,description) VALUES ('accounting.post','accounting','post','Post journal entries / documents');
        INSERT OR IGNORE INTO permissions(key,module,action,description) VALUES ('accounting.close_period','accounting','close_period','Close accounting periods');
        INSERT OR IGNORE INTO permissions(key,module,action,description) VALUES ('settings.manage','settings','manage','Manage system settings');
        INSERT OR IGNORE INTO permissions(key,module,action,description) VALUES ('users.manage','users','manage','Manage users and roles');
    """)

    cursor.executescript("""
        INSERT OR IGNORE INTO role_permissions(role_id, permission_key, allowed)
        SELECT r.id, p.key, 1 FROM roles r CROSS JOIN permissions p WHERE r.name='admin';
        INSERT OR IGNORE INTO role_permissions(role_id, permission_key, allowed)
        SELECT r.id, p.key, 1 FROM roles r JOIN permissions p ON p.key IN (
            'reports.view','reports.export','invoices.edit','returns.edit','branches.view_all','approval.submit','approval.approve','approval.reject'
        ) WHERE r.name='manager';
        INSERT OR IGNORE INTO role_permissions(role_id, permission_key, allowed)
        SELECT r.id, p.key, 1 FROM roles r JOIN permissions p ON p.key IN (
            'reports.view','reports.export','accounting.view','accounting.post','accounting.close_period','approval.submit'
        ) WHERE r.name='accountant';
        INSERT OR IGNORE INTO role_permissions(role_id, permission_key, allowed)
        SELECT r.id, p.key, 1 FROM roles r JOIN permissions p ON p.key IN ('approval.submit') WHERE r.name='cashier';
        INSERT OR IGNORE INTO role_permissions(role_id, permission_key, allowed)
        SELECT r.id, p.key, 1 FROM roles r JOIN permissions p ON p.key IN ('reports.view') WHERE r.name='viewer';
        INSERT OR IGNORE INTO user_roles(user_id, role_id)
        SELECT u.id, r.id FROM users u JOIN roles r ON lower(COALESCE(u.role,'user')) = r.name;
    """)


    _phase158_159_schema(conn)
    conn.commit()
    conn.close()
    print(f"✅ تم تهيئة قاعدة بيانات الخادم في: {DB_PATH}")


def _phase158_159_schema(conn):
    """Phase 158/159: enterprise governance, health, recovery/stress support.

    Idempotent schema patch for both fresh and upgraded databases.
    """
    cur = conn.cursor()
    def _table_exists(name):
        cur.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND lower(name)=lower(?) LIMIT 1", (name,))
        return cur.fetchone() is not None
    def _columns(name):
        if not _table_exists(name):
            return set()
        cur.execute(f"PRAGMA table_info({name})")
        return {row[1] for row in cur.fetchall()}
    def _add_col(table, col, ddl):
        if _table_exists(table) and col not in _columns(table):
            cur.execute(f"ALTER TABLE {table} ADD COLUMN {col} {ddl}")
    cur.executescript("""

        CREATE TABLE IF NOT EXISTS approval_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entity_type TEXT NOT NULL,
            entity_id INTEGER NOT NULL,
            amount TEXT DEFAULT '0',
            threshold_amount TEXT DEFAULT '0',
            status TEXT NOT NULL DEFAULT 'PENDING',
            requested_by TEXT,
            requested_at TEXT,
            decided_by TEXT,
            decided_at TEXT,
            decision_notes TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT,
            UNIQUE(entity_type, entity_id)
        );
        CREATE INDEX IF NOT EXISTS idx_approval_requests_status ON approval_requests(status, entity_type);
        CREATE TABLE IF NOT EXISTS accounts (id INTEGER PRIMARY KEY AUTOINCREMENT, code TEXT UNIQUE NOT NULL, name TEXT NOT NULL, type TEXT NOT NULL, parent_id INTEGER, is_active INTEGER DEFAULT 1, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS journal_entries (id INTEGER PRIMARY KEY AUTOINCREMENT, entry_no TEXT UNIQUE, entry_date TEXT NOT NULL DEFAULT CURRENT_DATE, source_type TEXT, source_id INTEGER, description TEXT, status TEXT DEFAULT 'POSTED', created_by TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP, UNIQUE(source_type, source_id));
        CREATE TABLE IF NOT EXISTS journal_lines (id INTEGER PRIMARY KEY AUTOINCREMENT, journal_entry_id INTEGER NOT NULL, account_id INTEGER NOT NULL, debit TEXT DEFAULT '0', credit TEXT DEFAULT '0', memo TEXT, FOREIGN KEY(journal_entry_id) REFERENCES journal_entries(id) ON DELETE CASCADE, FOREIGN KEY(account_id) REFERENCES accounts(id));
        CREATE INDEX IF NOT EXISTS idx_journal_entries_source ON journal_entries(source_type, source_id);
        INSERT OR IGNORE INTO accounts(code, name, type) VALUES ('1000','Cash / صندوق','ASSET');
        INSERT OR IGNORE INTO accounts(code, name, type) VALUES ('1100','Accounts Receivable / ذمم العملاء','ASSET');
        INSERT OR IGNORE INTO accounts(code, name, type) VALUES ('1200','Inventory / مخزون','ASSET');
        INSERT OR IGNORE INTO accounts(code, name, type) VALUES ('2000','Accounts Payable / ذمم الموردين','LIABILITY');
        INSERT OR IGNORE INTO accounts(code, name, type) VALUES ('3000','Owner Equity / حقوق الملكية','EQUITY');
        INSERT OR IGNORE INTO accounts(code, name, type) VALUES ('3100','Retained Earnings / أرباح مرحلة','EQUITY');
        INSERT OR IGNORE INTO accounts(code, name, type) VALUES ('4000','Sales Revenue / إيرادات المبيعات','REVENUE');
        INSERT OR IGNORE INTO accounts(code, name, type) VALUES ('5000','Purchases / مشتريات','EXPENSE');
        CREATE TABLE IF NOT EXISTS approval_matrix (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_type TEXT NOT NULL DEFAULT 'INVOICE',
            invoice_type TEXT,
            min_amount TEXT DEFAULT '0',
            max_amount TEXT,
            required_role TEXT NOT NULL,
            required_permission TEXT DEFAULT 'approval.approve',
            approval_order INTEGER NOT NULL DEFAULT 1,
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS approval_steps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            approval_request_id INTEGER NOT NULL,
            step_order INTEGER NOT NULL,
            required_role TEXT NOT NULL,
            required_permission TEXT DEFAULT 'approval.approve',
            status TEXT DEFAULT 'PENDING',
            decided_by TEXT,
            decided_at TEXT,
            notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(approval_request_id, step_order),
            FOREIGN KEY(approval_request_id) REFERENCES approval_requests(id) ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS idx_approval_steps_request
            ON approval_steps(approval_request_id, status, step_order);

        CREATE TABLE IF NOT EXISTS system_health_checks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            check_key TEXT NOT NULL,
            status TEXT NOT NULL,
            message TEXT,
            details TEXT,
            checked_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_system_health_checks_key
            ON system_health_checks(check_key, checked_at);

        CREATE TABLE IF NOT EXISTS validation_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_type TEXT NOT NULL,
            status TEXT NOT NULL,
            summary TEXT,
            details TEXT,
            started_at TEXT DEFAULT CURRENT_TIMESTAMP,
            finished_at TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_validation_runs_type
            ON validation_runs(run_type, started_at);
    """)
    _add_col('approval_matrix', 'invoice_type', 'TEXT')
    _add_col('approval_matrix', 'min_amount', "TEXT DEFAULT '0'")
    _add_col('approval_matrix', 'max_amount', 'TEXT')
    _add_col('approval_matrix', 'required_permission', "TEXT DEFAULT 'approval.approve'")
    _add_col('approval_matrix', 'approval_order', 'INTEGER DEFAULT 1')
    _add_col('approval_matrix', 'is_active', 'INTEGER DEFAULT 1')
    cur.execute('CREATE INDEX IF NOT EXISTS idx_approval_matrix_scope ON approval_matrix(document_type, invoice_type, is_active, approval_order)')
    _add_col('roles', 'parent_role_id', 'INTEGER')
    _add_col('roles', 'priority', 'INTEGER DEFAULT 0')
    _add_col('user_roles', 'branch_id', 'INTEGER')
    # Default hierarchy: viewer < cashier < accountant < manager < admin
    cur.executescript("""
        INSERT OR IGNORE INTO permissions(key,module,action,description) VALUES ('system.health.view','system','health_view','View system health center');
        INSERT OR IGNORE INTO permissions(key,module,action,description) VALUES ('system.validation.run','system','validation_run','Run backup/recovery/stress validations');
        INSERT OR IGNORE INTO permissions(key,module,action,description) VALUES ('approval.matrix.manage','approval','matrix_manage','Manage approval matrix');
        INSERT OR IGNORE INTO permissions(key,module,action,description) VALUES ('approval.level1','approval','level1','Approve first approval level');
        INSERT OR IGNORE INTO permissions(key,module,action,description) VALUES ('approval.level2','approval','level2','Approve second approval level');
        INSERT OR IGNORE INTO permissions(key,module,action,description) VALUES ('approval.level3','approval','level3','Approve third approval level');
    """)
    # safe hierarchy updates after roles exist
    roles = {r[1] if not hasattr(r, 'keys') else r['name']: (r[0] if not hasattr(r,'keys') else r['id']) for r in cur.execute("SELECT id, name FROM roles").fetchall()} if _table_exists('roles') else {}
    priorities = {'viewer':10,'cashier':20,'accountant':30,'manager':40,'admin':50}
    parent = {'cashier':'viewer','accountant':'cashier','manager':'accountant','admin':'manager'}
    for name, prio in priorities.items():
        cur.execute("UPDATE roles SET priority=? WHERE name=?", (prio, name))
        if name in parent and parent[name] in roles:
            cur.execute("UPDATE roles SET parent_role_id=? WHERE name=? AND (parent_role_id IS NULL OR parent_role_id=0)", (roles[parent[name]], name))
    cur.executescript("""
        INSERT OR IGNORE INTO role_permissions(role_id, permission_key, allowed)
        SELECT r.id, p.key, 1 FROM roles r JOIN permissions p ON p.key IN (
            'system.health.view','system.validation.run','approval.matrix.manage','approval.level1','approval.level2','approval.level3'
        ) WHERE r.name='admin';

        INSERT OR IGNORE INTO role_permissions(role_id, permission_key, allowed)
        SELECT r.id, p.key, 1 FROM roles r JOIN permissions p ON p.key IN (
            'system.health.view','approval.level1','approval.level2'
        ) WHERE r.name='manager';

        INSERT OR IGNORE INTO role_permissions(role_id, permission_key, allowed)
        SELECT r.id, p.key, 1 FROM roles r JOIN permissions p ON p.key IN (
            'system.health.view','approval.level1'
        ) WHERE r.name='accountant';
    """)
    # Default approval matrix: small -> manager/accountant level1; medium -> manager+accountant; large -> manager+accountant+admin
    cur.executescript("""
        INSERT OR IGNORE INTO approval_matrix(document_type, invoice_type, min_amount, max_amount, required_role, required_permission, approval_order, is_active)
        VALUES ('INVOICE','sale','0','5000','manager','approval.level1',1,1);
        INSERT OR IGNORE INTO approval_matrix(document_type, invoice_type, min_amount, max_amount, required_role, required_permission, approval_order, is_active)
        VALUES ('INVOICE','sale','5000','20000','manager','approval.level1',1,1);
        INSERT OR IGNORE INTO approval_matrix(document_type, invoice_type, min_amount, max_amount, required_role, required_permission, approval_order, is_active)
        VALUES ('INVOICE','sale','5000','20000','accountant','approval.level2',2,1);
        INSERT OR IGNORE INTO approval_matrix(document_type, invoice_type, min_amount, max_amount, required_role, required_permission, approval_order, is_active)
        VALUES ('INVOICE','sale','20000',NULL,'manager','approval.level1',1,1);
        INSERT OR IGNORE INTO approval_matrix(document_type, invoice_type, min_amount, max_amount, required_role, required_permission, approval_order, is_active)
        VALUES ('INVOICE','sale','20000',NULL,'accountant','approval.level2',2,1);
        INSERT OR IGNORE INTO approval_matrix(document_type, invoice_type, min_amount, max_amount, required_role, required_permission, approval_order, is_active)
        VALUES ('INVOICE','sale','20000',NULL,'admin','approval.level3',3,1);
    """)


def ensure_db():
    # init_database uses CREATE IF NOT EXISTS and safe ALTERs, so running it
    # every startup also upgrades existing databases.
    init_database()


