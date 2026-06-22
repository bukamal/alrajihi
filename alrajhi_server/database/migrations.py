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
            barcode TEXT,
            notes TEXT,
            FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE
        );


        CREATE TABLE IF NOT EXISTS item_variants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id INTEGER NOT NULL,
            color TEXT DEFAULT '',
            size TEXT DEFAULT '',
            sku TEXT,
            barcode TEXT,
            sale_price TEXT,
            cost_price TEXT,
            quantity TEXT DEFAULT '0',
            reorder_level TEXT DEFAULT '0',
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT,
            FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE,
            UNIQUE(item_id, color, size)
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
            variant_id INTEGER,
            variant_color TEXT,
            variant_size TEXT,
            variant_sku TEXT,
            barcode_scope TEXT,
            matched_barcode TEXT,
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
            variant_id INTEGER,
            variant_color TEXT,
            variant_size TEXT,
            variant_sku TEXT,
            barcode_scope TEXT,
            matched_barcode TEXT,
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
            conversion_factor TEXT DEFAULT '1',
            base_qty TEXT DEFAULT '0',
            barcode_scope TEXT,
            matched_barcode TEXT,
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
            unit_id INTEGER,
            conversion_factor TEXT DEFAULT '1',
            base_qty TEXT DEFAULT '0',
            barcode_scope TEXT,
            matched_barcode TEXT,
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
            unit_id INTEGER,
            unit_name TEXT,
            conversion_factor TEXT DEFAULT '1',
            consumed_base_qty TEXT DEFAULT '0',
            barcode_scope TEXT,
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
            unit_id INTEGER,
            unit_name TEXT,
            conversion_factor TEXT DEFAULT '1',
            produced_base_qty TEXT DEFAULT '0',
            barcode_scope TEXT,
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
            source TEXT,
            audit_scope TEXT,
            permission_key TEXT,
            branch_id INTEGER,
            event_category TEXT
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
        'CREATE INDEX IF NOT EXISTS idx_wh_variant_balances_variant ON item_warehouse_variant_balances(variant_id);',
        'CREATE INDEX IF NOT EXISTS idx_wh_variant_balances_wh ON item_warehouse_variant_balances(warehouse_id);',
        'CREATE INDEX IF NOT EXISTS idx_wh_mov_variant ON warehouse_movements(variant_id);',
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
    migrate_phase260_rbac_contract_permissions(conn)
    migrate_phase264_audit_contract_columns(conn)
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
    cur.executescript("""



        -- Phase182: Restaurant operation-level permissions.
        INSERT OR IGNORE INTO permissions(key,module,action,description) VALUES ('restaurant.use','restaurant','use','Use Restaurant POS');
        INSERT OR IGNORE INTO permissions(key,module,action,description) VALUES ('restaurant.session.open','restaurant','session_open','Open restaurant sessions');
        INSERT OR IGNORE INTO permissions(key,module,action,description) VALUES ('restaurant.line.add','restaurant','line_add','Add restaurant order lines');
        INSERT OR IGNORE INTO permissions(key,module,action,description) VALUES ('restaurant.kitchen.send','restaurant','kitchen_send','Send restaurant orders to kitchen');
        INSERT OR IGNORE INTO permissions(key,module,action,description) VALUES ('restaurant.bill.adjust','restaurant','bill_adjust','Adjust restaurant bills');
        INSERT OR IGNORE INTO permissions(key,module,action,description) VALUES ('restaurant.payment.record','restaurant','payment_record','Record restaurant payments');
        INSERT OR IGNORE INTO permissions(key,module,action,description) VALUES ('restaurant.checkout','restaurant','checkout','Checkout restaurant sessions');
        INSERT OR IGNORE INTO permissions(key,module,action,description) VALUES ('restaurant.kitchen.status.update','restaurant','kitchen_status_update','Update kitchen ticket status');
        INSERT OR IGNORE INTO role_permissions(role_id, permission_key, allowed)
        SELECT r.id, p.key, 1 FROM roles r JOIN permissions p ON p.key IN (
            'restaurant.use','restaurant.session.open','restaurant.line.add','restaurant.kitchen.send','restaurant.bill.adjust','restaurant.payment.record','restaurant.checkout','restaurant.kitchen.status.update'
        ) WHERE r.name IN ('admin','manager','cashier');



        -- Phase183: Restaurant print/export permissions.
        INSERT OR IGNORE INTO permissions(key,module,action,description) VALUES ('restaurant.receipt.print','restaurant','receipt_print','Print restaurant customer receipts');
        INSERT OR IGNORE INTO permissions(key,module,action,description) VALUES ('restaurant.kitchen_ticket.print','restaurant','kitchen_ticket_print','Print restaurant kitchen tickets');
        INSERT OR IGNORE INTO role_permissions(role_id, permission_key, allowed)
        SELECT r.id, p.key, 1 FROM roles r JOIN permissions p ON p.key IN (
            'restaurant.receipt.print','restaurant.kitchen_ticket.print'
        ) WHERE r.name IN ('admin','manager','cashier');



        -- Phase187: Manufacturing operation-level permissions.
        INSERT OR IGNORE INTO permissions(key,module,action,description) VALUES ('manufacturing.use','manufacturing','use','Use manufacturing module');
        INSERT OR IGNORE INTO permissions(key,module,action,description) VALUES ('manufacturing.bom.create','manufacturing','bom_create','Create BOM recipes');
        INSERT OR IGNORE INTO permissions(key,module,action,description) VALUES ('manufacturing.bom.edit','manufacturing','bom_edit','Edit BOM recipes');
        INSERT OR IGNORE INTO permissions(key,module,action,description) VALUES ('manufacturing.bom.delete','manufacturing','bom_delete','Delete BOM recipes');
        INSERT OR IGNORE INTO permissions(key,module,action,description) VALUES ('manufacturing.order.create','manufacturing','order_create','Create production orders');
        INSERT OR IGNORE INTO permissions(key,module,action,description) VALUES ('manufacturing.order.start','manufacturing','order_start','Start production orders');
        INSERT OR IGNORE INTO permissions(key,module,action,description) VALUES ('manufacturing.material.consume','manufacturing','material_consume','Consume production materials');
        INSERT OR IGNORE INTO permissions(key,module,action,description) VALUES ('manufacturing.output.complete','manufacturing','output_complete','Complete production outputs');
        INSERT OR IGNORE INTO permissions(key,module,action,description) VALUES ('manufacturing.order.cancel','manufacturing','order_cancel','Cancel production orders');
        INSERT OR IGNORE INTO permissions(key,module,action,description) VALUES ('manufacturing.order.delete','manufacturing','order_delete','Delete production orders');
        INSERT OR IGNORE INTO permissions(key,module,action,description) VALUES ('manufacturing.order.reverse','manufacturing','order_reverse','Reverse completed production orders');
        INSERT OR IGNORE INTO permissions(key,module,action,description) VALUES ('manufacturing.consumption.delete','manufacturing','consumption_delete','Delete production material consumptions');
        INSERT OR IGNORE INTO permissions(key,module,action,description) VALUES ('manufacturing.output.delete','manufacturing','output_delete','Delete production outputs');
        INSERT OR IGNORE INTO permissions(key,module,action,description) VALUES ('manufacturing.cost.view','manufacturing','cost_view','View manufacturing costs');
        INSERT OR IGNORE INTO permissions(key,module,action,description) VALUES ('manufacturing.print','manufacturing','print','Print manufacturing documents');
        INSERT OR IGNORE INTO role_permissions(role_id, permission_key, allowed)
        SELECT r.id, p.key, 1 FROM roles r JOIN permissions p ON p.key IN (
            'manufacturing.use','manufacturing.bom.create','manufacturing.bom.edit','manufacturing.bom.delete',
            'manufacturing.order.create','manufacturing.order.start','manufacturing.material.consume','manufacturing.output.complete',
            'manufacturing.order.cancel','manufacturing.order.delete','manufacturing.order.reverse',
            'manufacturing.consumption.delete','manufacturing.output.delete','manufacturing.cost.view','manufacturing.print'
        ) WHERE r.name IN ('admin','manager');
        INSERT OR IGNORE INTO role_permissions(role_id, permission_key, allowed)
        SELECT r.id, p.key, 1 FROM roles r JOIN permissions p ON p.key IN (
            'manufacturing.use','manufacturing.cost.view','manufacturing.print'
        ) WHERE r.name='accountant';


        -- Phase194: Inventory / warehouse operation-level permissions.
        INSERT OR IGNORE INTO permissions(key,module,action,description) VALUES ('inventory.use','inventory','use','Use inventory and warehouse workspace');
        INSERT OR IGNORE INTO permissions(key,module,action,description) VALUES ('inventory.warehouse.create','inventory','warehouse_create','Create warehouses');
        INSERT OR IGNORE INTO permissions(key,module,action,description) VALUES ('inventory.warehouse.edit','inventory','warehouse_edit','Edit warehouses');
        INSERT OR IGNORE INTO permissions(key,module,action,description) VALUES ('inventory.warehouse.archive','inventory','warehouse_archive','Archive warehouses');
        INSERT OR IGNORE INTO permissions(key,module,action,description) VALUES ('inventory.balance.view','inventory','balance_view','View item balances');
        INSERT OR IGNORE INTO permissions(key,module,action,description) VALUES ('inventory.movement.view','inventory','movement_view','View stock movements');
        INSERT OR IGNORE INTO permissions(key,module,action,description) VALUES ('inventory.movement.direct','inventory','direct_movement','Post direct inventory movements');
        INSERT OR IGNORE INTO permissions(key,module,action,description) VALUES ('inventory.transfer.create','inventory','transfer_create','Create warehouse transfers');
        INSERT OR IGNORE INTO permissions(key,module,action,description) VALUES ('inventory.transfer.cancel','inventory','transfer_cancel','Cancel warehouse transfers');
        INSERT OR IGNORE INTO permissions(key,module,action,description) VALUES ('inventory.ledger.view','inventory','ledger_view','View inventory ledger');
        INSERT OR IGNORE INTO permissions(key,module,action,description) VALUES ('inventory.ledger.backfill','inventory','ledger_backfill','Backfill inventory ledger');
        INSERT OR IGNORE INTO permissions(key,module,action,description) VALUES ('inventory.reconcile','inventory','reconcile','Run inventory reconciliation');
        INSERT OR IGNORE INTO permissions(key,module,action,description) VALUES ('inventory.print','inventory','print','Print inventory and warehouse documents');

        -- Phase203/204: Finance, cashbox, bank, and voucher operation-level permissions.
        INSERT OR IGNORE INTO permissions(key,module,action,description) VALUES ('finance.use','finance','use','Use finance workspace');
        INSERT OR IGNORE INTO permissions(key,module,action,description) VALUES ('finance.cashbox.create','finance','cashbox_create','Create cashboxes');
        INSERT OR IGNORE INTO permissions(key,module,action,description) VALUES ('finance.cashbox.edit','finance','cashbox_edit','Edit cashboxes');
        INSERT OR IGNORE INTO permissions(key,module,action,description) VALUES ('finance.cashbox.archive','finance','cashbox_archive','Archive cashboxes');
        INSERT OR IGNORE INTO permissions(key,module,action,description) VALUES ('finance.bank.create','finance','bank_create','Create bank accounts');
        INSERT OR IGNORE INTO permissions(key,module,action,description) VALUES ('finance.bank.edit','finance','bank_edit','Edit bank accounts');
        INSERT OR IGNORE INTO permissions(key,module,action,description) VALUES ('finance.bank.archive','finance','bank_archive','Archive bank accounts');
        INSERT OR IGNORE INTO permissions(key,module,action,description) VALUES ('finance.movements.view','finance','movements_view','View finance movements');
        INSERT OR IGNORE INTO permissions(key,module,action,description) VALUES ('finance.shifts.view','finance','shifts_view','View cashbox shifts');
        INSERT OR IGNORE INTO permissions(key,module,action,description) VALUES ('finance.voucher.view','finance','voucher_view','View vouchers');
        INSERT OR IGNORE INTO permissions(key,module,action,description) VALUES ('finance.voucher.create','finance','voucher_create','Create vouchers');
        INSERT OR IGNORE INTO permissions(key,module,action,description) VALUES ('finance.voucher.edit','finance','voucher_edit','Edit vouchers');
        INSERT OR IGNORE INTO permissions(key,module,action,description) VALUES ('finance.voucher.delete','finance','voucher_delete','Delete vouchers');
        INSERT OR IGNORE INTO permissions(key,module,action,description) VALUES ('finance.voucher.print','finance','voucher_print','Print vouchers');
        INSERT OR IGNORE INTO permissions(key,module,action,description) VALUES ('finance.expense.view','finance','expense_view','View expenses');
        INSERT OR IGNORE INTO permissions(key,module,action,description) VALUES ('finance.expense.create','finance','expense_create','Create expenses');
        INSERT OR IGNORE INTO permissions(key,module,action,description) VALUES ('finance.expense.edit','finance','expense_edit','Edit expenses');
        INSERT OR IGNORE INTO permissions(key,module,action,description) VALUES ('finance.expense.delete','finance','expense_delete','Delete expenses');
        INSERT OR IGNORE INTO permissions(key,module,action,description) VALUES ('finance.expense.print','finance','expense_print','Print expenses');
        INSERT OR IGNORE INTO role_permissions(role_id, permission_key, allowed)
        SELECT r.id, p.key, 1 FROM roles r JOIN permissions p ON p.key IN (
            'inventory.use','inventory.warehouse.create','inventory.warehouse.edit','inventory.warehouse.archive',
            'inventory.balance.view','inventory.movement.view','inventory.movement.direct',
            'inventory.transfer.create','inventory.transfer.cancel','inventory.ledger.view','inventory.reconcile','inventory.print'
        ) WHERE r.name IN ('admin','manager');
        INSERT OR IGNORE INTO role_permissions(role_id, permission_key, allowed)
        SELECT r.id, p.key, 1 FROM roles r JOIN permissions p ON p.key IN (
            'inventory.use','inventory.balance.view','inventory.movement.view','inventory.ledger.view','inventory.print'
        ) WHERE r.name='accountant';
        INSERT OR IGNORE INTO role_permissions(role_id, permission_key, allowed)
        SELECT r.id, p.key, 1 FROM roles r JOIN permissions p ON p.key IN (
            'inventory.use','inventory.balance.view','inventory.transfer.create','inventory.print'
        ) WHERE r.name='cashier';
        INSERT OR IGNORE INTO role_permissions(role_id, permission_key, allowed)
        SELECT r.id, p.key, 1 FROM roles r JOIN permissions p ON p.key IN (
            'finance.use','finance.cashbox.create','finance.cashbox.edit','finance.cashbox.archive',
            'finance.bank.create','finance.bank.edit','finance.bank.archive','finance.movements.view','finance.shifts.view',
            'finance.voucher.view','finance.voucher.create','finance.voucher.edit','finance.voucher.delete','finance.voucher.print',
            'finance.expense.view','finance.expense.create','finance.expense.edit','finance.expense.delete','finance.expense.print'
        ) WHERE r.name IN ('admin','manager');
        INSERT OR IGNORE INTO role_permissions(role_id, permission_key, allowed)
        SELECT r.id, p.key, 1 FROM roles r JOIN permissions p ON p.key IN (
            'finance.use','finance.movements.view','finance.voucher.view','finance.voucher.create','finance.voucher.edit','finance.voucher.print',
            'finance.expense.view','finance.expense.create','finance.expense.edit','finance.expense.print'
        ) WHERE r.name='accountant';
        INSERT OR IGNORE INTO role_permissions(role_id, permission_key, allowed)
        SELECT r.id, p.key, 1 FROM roles r JOIN permissions p ON p.key IN (
            'finance.use','finance.voucher.view','finance.voucher.create','finance.voucher.print',
            'finance.expense.view','finance.expense.create','finance.expense.print'
        ) WHERE r.name='cashier';

        -- Phase178: POS operation-level permissions.
        INSERT OR IGNORE INTO permissions(key,module,action,description) VALUES ('pos.use','pos','use','Use POS');
        INSERT OR IGNORE INTO permissions(key,module,action,description) VALUES ('pos.suspend','pos','suspend','Suspend POS sales');
        INSERT OR IGNORE INTO permissions(key,module,action,description) VALUES ('pos.resume','pos','resume','Resume suspended POS sales');
        INSERT OR IGNORE INTO permissions(key,module,action,description) VALUES ('pos.line.remove','pos','line_remove','Remove POS lines');
        INSERT OR IGNORE INTO permissions(key,module,action,description) VALUES ('pos.cart.clear','pos','cart_clear','Clear POS carts');
        INSERT OR IGNORE INTO permissions(key,module,action,description) VALUES ('pos.shift.open','pos','shift_open','Open POS shifts');
        INSERT OR IGNORE INTO permissions(key,module,action,description) VALUES ('pos.shift.close','pos','shift_close','Close POS shifts');
        INSERT OR IGNORE INTO permissions(key,module,action,description) VALUES ('pos.receipt.print','pos','receipt_print','Print POS receipts');
        INSERT OR IGNORE INTO role_permissions(role_id, permission_key, allowed)
        SELECT r.id, p.key, 1 FROM roles r JOIN permissions p ON p.key IN (
            'pos.use','pos.suspend','pos.resume','pos.line.remove','pos.cart.clear','pos.shift.open','pos.shift.close','pos.receipt.print'
        ) WHERE r.name IN ('admin','manager','cashier');
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



def migrate_phase260_rbac_contract_permissions(conn):
    """Phase260: seed canonical permissions required by Shell/List/Report/Operational contracts.

    This is intentionally server-side and idempotent.  It closes the gap between
    UI contract permissions such as ``sales_invoices.update`` and older generic
    permissions such as ``invoices.edit``.  Existing role customizations are not
    removed; the migration only inserts missing permissions and merges the
    default system-role grants.
    """
    cur = conn.cursor()
    rows = [
        ('bank_accounts.create', 'bank_accounts', 'create', 'document:bank_account:create: bank_accounts create'),
        ('bank_accounts.delete', 'bank_accounts', 'delete', 'document:bank_account:delete: bank_accounts delete'),
        ('bank_accounts.update', 'bank_accounts', 'update', 'document:bank_account:update: bank_accounts update'),
        ('bank_accounts.view', 'bank_accounts', 'view', 'document:bank_account:view: bank_accounts view'),
        ('branches.create', 'branches', 'create', 'document:branch:create: branches create'),
        ('branches.delete', 'branches', 'delete', 'document:branch:delete: branches delete'),
        ('branches.manage_all', 'branches', 'manage_all', 'rbac:branch_scope:manage_all: branches manage all'),
        ('branches.update', 'branches', 'update', 'document:branch:update: branches update'),
        ('branches.view', 'branches', 'view', 'document:branch:view: branches view'),
        ('branches.view_all', 'branches', 'view_all', 'rbac:branch_scope:view_all: branches view all'),
        ('cashboxes.create', 'cashboxes', 'create', 'document:cashbox:create: cashboxes create'),
        ('cashboxes.delete', 'cashboxes', 'delete', 'document:cashbox:delete: cashboxes delete'),
        ('cashboxes.update', 'cashboxes', 'update', 'document:cashbox:update: cashboxes update'),
        ('cashboxes.view', 'cashboxes', 'view', 'document:cashbox:view: cashboxes view'),
        ('cafe.order', 'cafe', 'order', 'document:cafe:create: cafe order'),
        ('cafe.payment', 'cafe', 'payment', 'document:cafe:update: cafe payment'),
        ('cafe.print', 'cafe', 'print', 'document:cafe:print: cafe print'),
        ('cafe.report', 'cafe', 'report', 'document:cafe:export: cafe report'),
        ('cafe.view', 'cafe', 'view', 'document:cafe:view: cafe view'),
        ('apparel.export', 'apparel', 'export', 'document:apparel:export: apparel export'),
        ('apparel.variant', 'apparel', 'variant', 'document:apparel:create: apparel variant'),
        ('apparel.variant.update', 'apparel', 'variant_update', 'document:apparel:update: apparel variant update'),
        ('apparel.view', 'apparel', 'view', 'document:apparel:view: apparel view'),
        ('categories.create', 'categories', 'create', 'document:category:create: categories create'),
        ('categories.delete', 'categories', 'delete', 'document:category:delete: categories delete'),
        ('categories.update', 'categories', 'update', 'document:category:update: categories update'),
        ('categories.view', 'categories', 'view', 'document:category:view: categories view'),
        ('customers.create', 'customers', 'create', 'document:customer:create: customers create'),
        ('customers.delete', 'customers', 'delete', 'document:customer:delete: customers delete'),
        ('customers.export', 'customers', 'export', 'document:customer:export: customers export'),
        ('customers.print', 'customers', 'print', 'document:customer:print: customers print'),
        ('customers.update', 'customers', 'update', 'document:customer:update: customers update'),
        ('customers.view', 'customers', 'view', 'document:customer:view: customers view'),
        ('expenses.cancel', 'expenses', 'cancel', 'document:expense:cancel: expenses cancel'),
        ('expenses.create', 'expenses', 'create', 'document:expense:create: expenses create'),
        ('expenses.delete', 'expenses', 'delete', 'document:expense:delete: expenses delete'),
        ('expenses.export', 'expenses', 'export', 'document:expense:export: expenses export'),
        ('expenses.print', 'expenses', 'print', 'document:expense:print: expenses print'),
        ('expenses.update', 'expenses', 'update', 'document:expense:update: expenses update'),
        ('expenses.view', 'expenses', 'view', 'document:expense:view: expenses view'),
        ('items.create', 'items', 'create', 'document:material:create: items create'),
        ('items.delete', 'items', 'delete', 'document:material:delete: items delete'),
        ('items.export', 'items', 'export', 'document:material:export: items export'),
        ('items.print', 'items', 'print', 'document:material:print: items print'),
        ('items.update', 'items', 'update', 'document:material:update: items update'),
        ('items.view', 'items', 'view', 'document:material:view: items view'),
        ('manufacturing.bom.approve', 'manufacturing', 'bom_approve', 'document:bom:approve: manufacturing bom approve'),
        ('manufacturing.bom.cancel', 'manufacturing', 'bom_cancel', 'document:bom:cancel: manufacturing bom cancel'),
        ('manufacturing.bom.create', 'manufacturing', 'bom_create', 'document:bom:create: manufacturing bom create'),
        ('manufacturing.bom.delete', 'manufacturing', 'bom_delete', 'document:bom:delete: manufacturing bom delete'),
        ('manufacturing.bom.export', 'manufacturing', 'bom_export', 'document:bom:export: manufacturing bom export'),
        ('manufacturing.bom.print', 'manufacturing', 'bom_print', 'document:bom:print: manufacturing bom print'),
        ('manufacturing.bom.update', 'manufacturing', 'bom_update', 'document:bom:update: manufacturing bom update'),
        ('manufacturing.bom.view', 'manufacturing', 'bom_view', 'document:bom:view: manufacturing bom view'),
        ('manufacturing.production_orders.approve', 'manufacturing', 'production_orders_approve', 'document:production_order:approve: manufacturing production orders approve'),
        ('manufacturing.production_orders.cancel', 'manufacturing', 'production_orders_cancel', 'document:production_order:cancel: manufacturing production orders cancel'),
        ('manufacturing.production_orders.create', 'manufacturing', 'production_orders_create', 'document:production_order:create: manufacturing production orders create'),
        ('manufacturing.production_orders.export', 'manufacturing', 'production_orders_export', 'document:production_order:export: manufacturing production orders export'),
        ('manufacturing.production_orders.print', 'manufacturing', 'production_orders_print', 'document:production_order:print: manufacturing production orders print'),
        ('manufacturing.production_orders.update', 'manufacturing', 'production_orders_update', 'document:production_order:update: manufacturing production orders update'),
        ('manufacturing.production_orders.view', 'manufacturing', 'production_orders_view', 'document:production_order:view: manufacturing production orders view'),
        ('pos.cart.clear', 'pos', 'cart_clear', 'operational:pos:clear_cart: pos cart clear'),
        ('pos.checkout', 'pos', 'checkout', 'document:pos:create: pos checkout'),
        ('pos.line.remove', 'pos', 'line_remove', 'operational:pos:remove_line: pos line remove'),
        ('pos.print', 'pos', 'print', 'document:pos:print: pos print'),
        ('pos.receipt.print', 'pos', 'receipt_print', 'operational:pos:print_receipt: pos receipt print'),
        ('pos.resume', 'pos', 'resume', 'operational:pos:resume: pos resume'),
        ('pos.shift.close', 'pos', 'shift_close', 'operational:pos:close_shift: pos shift close'),
        ('pos.shift.open', 'pos', 'shift_open', 'operational:pos:open_shift: pos shift open'),
        ('pos.suspend', 'pos', 'suspend', 'operational:pos:suspend: pos suspend'),
        ('pos.use', 'pos', 'use', 'operational:pos:checkout: pos use'),
        ('pos.view', 'pos', 'view', 'document:pos:view: pos view'),
        ('pos.void', 'pos', 'void', 'document:pos:cancel: pos void'),
        ('purchase_invoices.approve', 'purchase_invoices', 'approve', 'document:purchase_invoice:approve: purchase_invoices approve'),
        ('purchase_invoices.cancel', 'purchase_invoices', 'cancel', 'document:purchase_invoice:cancel: purchase_invoices cancel'),
        ('purchase_invoices.create', 'purchase_invoices', 'create', 'document:purchase_invoice:create: purchase_invoices create'),
        ('purchase_invoices.delete', 'purchase_invoices', 'delete', 'document:purchase_invoice:delete: purchase_invoices delete'),
        ('purchase_invoices.export', 'purchase_invoices', 'export', 'document:purchase_invoice:export: purchase_invoices export'),
        ('purchase_invoices.print', 'purchase_invoices', 'print', 'document:purchase_invoice:print: purchase_invoices print'),
        ('purchase_invoices.update', 'purchase_invoices', 'update', 'document:purchase_invoice:update: purchase_invoices update'),
        ('purchase_invoices.view', 'purchase_invoices', 'view', 'document:purchase_invoice:view: purchase_invoices view'),
        ('purchase_returns.approve', 'purchase_returns', 'approve', 'document:purchase_return:approve: purchase_returns approve'),
        ('purchase_returns.cancel', 'purchase_returns', 'cancel', 'document:purchase_return:cancel: purchase_returns cancel'),
        ('purchase_returns.create', 'purchase_returns', 'create', 'document:purchase_return:create: purchase_returns create'),
        ('purchase_returns.delete', 'purchase_returns', 'delete', 'document:purchase_return:delete: purchase_returns delete'),
        ('purchase_returns.export', 'purchase_returns', 'export', 'document:purchase_return:export: purchase_returns export'),
        ('purchase_returns.print', 'purchase_returns', 'print', 'document:purchase_return:print: purchase_returns print'),
        ('purchase_returns.update', 'purchase_returns', 'update', 'document:purchase_return:update: purchase_returns update'),
        ('purchase_returns.view', 'purchase_returns', 'view', 'document:purchase_return:view: purchase_returns view'),
        ('reports.export', 'reports', 'export', 'document:reports:export: reports export'),
        ('reports.print', 'reports', 'print', 'document:reports:print: reports print'),
        ('reports.view', 'reports', 'view', 'document:reports:view: reports view'),
        ('restaurant.bill.adjust', 'restaurant', 'bill_adjust', 'operational:restaurant:adjust_bill: restaurant bill adjust'),
        ('restaurant.cancel', 'restaurant', 'cancel', 'document:restaurant:cancel: restaurant cancel'),
        ('restaurant.checkout', 'restaurant', 'checkout', 'operational:restaurant:checkout: restaurant checkout'),
        ('restaurant.kitchen.send', 'restaurant', 'kitchen_send', 'operational:restaurant:send_kitchen: restaurant kitchen send'),
        ('restaurant.kitchen.status.update', 'restaurant', 'kitchen_status_update', 'operational:restaurant:update_kitchen_status: restaurant kitchen status update'),
        ('restaurant.kitchen_ticket.print', 'restaurant', 'kitchen_ticket_print', 'operational:restaurant:print_kitchen_ticket: restaurant kitchen ticket print'),
        ('restaurant.line.add', 'restaurant', 'line_add', 'operational:restaurant:add_line: restaurant line add'),
        ('restaurant.order', 'restaurant', 'order', 'document:restaurant:create: restaurant order'),
        ('restaurant.order.update', 'restaurant', 'order_update', 'document:restaurant:update: restaurant order update'),
        ('restaurant.payment.record', 'restaurant', 'payment_record', 'operational:restaurant:record_payment: restaurant payment record'),
        ('restaurant.print', 'restaurant', 'print', 'document:restaurant:print: restaurant print'),
        ('restaurant.receipt.print', 'restaurant', 'receipt_print', 'operational:restaurant:print_receipt: restaurant receipt print'),
        ('restaurant.session.open', 'restaurant', 'session_open', 'operational:restaurant:open_session: restaurant session open'),
        ('restaurant.use', 'restaurant', 'use', 'operational:restaurant:use: restaurant use'),
        ('restaurant.view', 'restaurant', 'view', 'document:restaurant:view: restaurant view'),
        ('sales_invoices.approve', 'sales_invoices', 'approve', 'document:sales_invoice:approve: sales_invoices approve'),
        ('sales_invoices.cancel', 'sales_invoices', 'cancel', 'document:sales_invoice:cancel: sales_invoices cancel'),
        ('sales_invoices.create', 'sales_invoices', 'create', 'document:sales_invoice:create: sales_invoices create'),
        ('sales_invoices.delete', 'sales_invoices', 'delete', 'document:sales_invoice:delete: sales_invoices delete'),
        ('sales_invoices.export', 'sales_invoices', 'export', 'document:sales_invoice:export: sales_invoices export'),
        ('sales_invoices.print', 'sales_invoices', 'print', 'document:sales_invoice:print: sales_invoices print'),
        ('sales_invoices.update', 'sales_invoices', 'update', 'document:sales_invoice:update: sales_invoices update'),
        ('sales_invoices.view', 'sales_invoices', 'view', 'document:sales_invoice:view: sales_invoices view'),
        ('sales_returns.approve', 'sales_returns', 'approve', 'document:sales_return:approve: sales_returns approve'),
        ('sales_returns.cancel', 'sales_returns', 'cancel', 'document:sales_return:cancel: sales_returns cancel'),
        ('sales_returns.create', 'sales_returns', 'create', 'document:sales_return:create: sales_returns create'),
        ('sales_returns.delete', 'sales_returns', 'delete', 'document:sales_return:delete: sales_returns delete'),
        ('sales_returns.export', 'sales_returns', 'export', 'document:sales_return:export: sales_returns export'),
        ('sales_returns.print', 'sales_returns', 'print', 'document:sales_return:print: sales_returns print'),
        ('sales_returns.update', 'sales_returns', 'update', 'document:sales_return:update: sales_returns update'),
        ('sales_returns.view', 'sales_returns', 'view', 'document:sales_return:view: sales_returns view'),
        ('settings.export', 'settings', 'export', 'document:settings_section:export: settings export'),
        ('settings.update', 'settings', 'update', 'document:settings_section:update: settings update'),
        ('settings.view', 'settings', 'view', 'document:settings_section:view: settings view'),
        ('suppliers.create', 'suppliers', 'create', 'document:supplier:create: suppliers create'),
        ('suppliers.delete', 'suppliers', 'delete', 'document:supplier:delete: suppliers delete'),
        ('suppliers.export', 'suppliers', 'export', 'document:supplier:export: suppliers export'),
        ('suppliers.print', 'suppliers', 'print', 'document:supplier:print: suppliers print'),
        ('suppliers.update', 'suppliers', 'update', 'document:supplier:update: suppliers update'),
        ('suppliers.view', 'suppliers', 'view', 'document:supplier:view: suppliers view'),
        ('users.create', 'users', 'create', 'document:user:create: users create'),
        ('users.delete', 'users', 'delete', 'document:user:delete: users delete'),
        ('users.update', 'users', 'update', 'document:user:update: users update'),
        ('users.view', 'users', 'view', 'document:user:view: users view'),
        ('vouchers.approve', 'vouchers', 'approve', 'document:voucher:approve: vouchers approve'),
        ('vouchers.cancel', 'vouchers', 'cancel', 'document:voucher:cancel: vouchers cancel'),
        ('vouchers.create', 'vouchers', 'create', 'document:voucher:create: vouchers create'),
        ('vouchers.delete', 'vouchers', 'delete', 'document:voucher:delete: vouchers delete'),
        ('vouchers.export', 'vouchers', 'export', 'document:voucher:export: vouchers export'),
        ('vouchers.print', 'vouchers', 'print', 'document:voucher:print: vouchers print'),
        ('vouchers.update', 'vouchers', 'update', 'document:voucher:update: vouchers update'),
        ('vouchers.view', 'vouchers', 'view', 'document:voucher:view: vouchers view'),
        ('warehouse_transfers.cancel', 'warehouse_transfers', 'cancel', 'document:warehouse_transfer:cancel: warehouse_transfers cancel'),
        ('warehouse_transfers.create', 'warehouse_transfers', 'create', 'document:warehouse_transfer:create: warehouse_transfers create'),
        ('warehouse_transfers.export', 'warehouse_transfers', 'export', 'document:warehouse_transfer:export: warehouse_transfers export'),
        ('warehouse_transfers.print', 'warehouse_transfers', 'print', 'document:warehouse_transfer:print: warehouse_transfers print'),
        ('warehouse_transfers.update', 'warehouse_transfers', 'update', 'document:warehouse_transfer:update: warehouse_transfers update'),
        ('warehouse_transfers.view', 'warehouse_transfers', 'view', 'document:warehouse_transfer:view: warehouse_transfers view'),
        ('warehouses.create', 'warehouses', 'create', 'document:warehouse:create: warehouses create'),
        ('warehouses.delete', 'warehouses', 'delete', 'document:warehouse:delete: warehouses delete'),
        ('warehouses.export', 'warehouses', 'export', 'document:warehouse:export: warehouses export'),
        ('warehouses.print', 'warehouses', 'print', 'document:warehouse:print: warehouses print'),
        ('warehouses.update', 'warehouses', 'update', 'document:warehouse:update: warehouses update'),
        ('warehouses.view', 'warehouses', 'view', 'document:warehouse:view: warehouses view')
    ]
    cur.executemany(
        "INSERT OR IGNORE INTO permissions(key,module,action,description) VALUES (?,?,?,?)",
        rows,
    )
    role_permissions = {
        'admin': (
            'bank_accounts.create',
            'bank_accounts.delete',
            'bank_accounts.update',
            'bank_accounts.view',
            'branches.create',
            'branches.delete',
            'branches.manage_all',
            'branches.update',
            'branches.view',
            'branches.view_all',
            'cashboxes.create',
            'cashboxes.delete',
            'cashboxes.update',
            'cashboxes.view',
            'categories.create',
            'categories.delete',
            'categories.update',
            'categories.view',
            'customers.create',
            'customers.delete',
            'customers.export',
            'customers.print',
            'customers.update',
            'customers.view',
            'expenses.cancel',
            'expenses.create',
            'expenses.delete',
            'expenses.export',
            'expenses.print',
            'expenses.update',
            'expenses.view',
            'items.create',
            'items.delete',
            'items.export',
            'items.print',
            'items.update',
            'items.view',
            'manufacturing.bom.approve',
            'manufacturing.bom.cancel',
            'manufacturing.bom.create',
            'manufacturing.bom.delete',
            'manufacturing.bom.export',
            'manufacturing.bom.print',
            'manufacturing.bom.update',
            'manufacturing.bom.view',
            'manufacturing.production_orders.approve',
            'manufacturing.production_orders.cancel',
            'manufacturing.production_orders.create',
            'manufacturing.production_orders.export',
            'manufacturing.production_orders.print',
            'manufacturing.production_orders.update',
            'manufacturing.production_orders.view',
            'pos.cart.clear',
            'pos.checkout',
            'pos.line.remove',
            'pos.print',
            'pos.receipt.print',
            'pos.resume',
            'pos.shift.close',
            'pos.shift.open',
            'pos.suspend',
            'pos.use',
            'pos.view',
            'pos.void',
            'purchase_invoices.approve',
            'purchase_invoices.cancel',
            'purchase_invoices.create',
            'purchase_invoices.delete',
            'purchase_invoices.export',
            'purchase_invoices.print',
            'purchase_invoices.update',
            'purchase_invoices.view',
            'purchase_returns.approve',
            'purchase_returns.cancel',
            'purchase_returns.create',
            'purchase_returns.delete',
            'purchase_returns.export',
            'purchase_returns.print',
            'purchase_returns.update',
            'purchase_returns.view',
            'reports.export',
            'reports.print',
            'reports.view',
            'restaurant.bill.adjust',
            'restaurant.cancel',
            'restaurant.checkout',
            'restaurant.kitchen.send',
            'restaurant.kitchen.status.update',
            'restaurant.kitchen_ticket.print',
            'restaurant.line.add',
            'restaurant.order',
            'restaurant.order.update',
            'restaurant.payment.record',
            'restaurant.print',
            'restaurant.receipt.print',
            'restaurant.session.open',
            'restaurant.use',
            'restaurant.view',
            'sales_invoices.approve',
            'sales_invoices.cancel',
            'sales_invoices.create',
            'sales_invoices.delete',
            'sales_invoices.export',
            'sales_invoices.print',
            'sales_invoices.update',
            'sales_invoices.view',
            'sales_returns.approve',
            'sales_returns.cancel',
            'sales_returns.create',
            'sales_returns.delete',
            'sales_returns.export',
            'sales_returns.print',
            'sales_returns.update',
            'sales_returns.view',
            'settings.export',
            'settings.update',
            'settings.view',
            'suppliers.create',
            'suppliers.delete',
            'suppliers.export',
            'suppliers.print',
            'suppliers.update',
            'suppliers.view',
            'users.create',
            'users.delete',
            'users.update',
            'users.view',
            'vouchers.approve',
            'vouchers.cancel',
            'vouchers.create',
            'vouchers.delete',
            'vouchers.export',
            'vouchers.print',
            'vouchers.update',
            'vouchers.view',
            'warehouse_transfers.cancel',
            'warehouse_transfers.create',
            'warehouse_transfers.export',
            'warehouse_transfers.print',
            'warehouse_transfers.update',
            'warehouse_transfers.view',
            'warehouses.create',
            'warehouses.delete',
            'warehouses.export',
            'warehouses.print',
            'warehouses.update',
            'warehouses.view',
        ),
        'manager': (
            'bank_accounts.create',
            'bank_accounts.delete',
            'bank_accounts.update',
            'bank_accounts.view',
            'branches.create',
            'branches.delete',
            'branches.manage_all',
            'branches.update',
            'branches.view',
            'branches.view_all',
            'cashboxes.create',
            'cashboxes.delete',
            'cashboxes.update',
            'cashboxes.view',
            'categories.create',
            'categories.delete',
            'categories.update',
            'categories.view',
            'customers.create',
            'customers.delete',
            'customers.export',
            'customers.print',
            'customers.update',
            'customers.view',
            'expenses.cancel',
            'expenses.create',
            'expenses.delete',
            'expenses.export',
            'expenses.print',
            'expenses.update',
            'expenses.view',
            'items.create',
            'items.delete',
            'items.export',
            'items.print',
            'items.update',
            'items.view',
            'manufacturing.bom.approve',
            'manufacturing.bom.cancel',
            'manufacturing.bom.create',
            'manufacturing.bom.delete',
            'manufacturing.bom.export',
            'manufacturing.bom.print',
            'manufacturing.bom.update',
            'manufacturing.bom.view',
            'manufacturing.production_orders.approve',
            'manufacturing.production_orders.cancel',
            'manufacturing.production_orders.create',
            'manufacturing.production_orders.export',
            'manufacturing.production_orders.print',
            'manufacturing.production_orders.update',
            'manufacturing.production_orders.view',
            'pos.cart.clear',
            'pos.checkout',
            'pos.line.remove',
            'pos.print',
            'pos.receipt.print',
            'pos.resume',
            'pos.shift.close',
            'pos.shift.open',
            'pos.suspend',
            'pos.use',
            'pos.view',
            'pos.void',
            'purchase_invoices.approve',
            'purchase_invoices.cancel',
            'purchase_invoices.create',
            'purchase_invoices.delete',
            'purchase_invoices.export',
            'purchase_invoices.print',
            'purchase_invoices.update',
            'purchase_invoices.view',
            'purchase_returns.approve',
            'purchase_returns.cancel',
            'purchase_returns.create',
            'purchase_returns.delete',
            'purchase_returns.export',
            'purchase_returns.print',
            'purchase_returns.update',
            'purchase_returns.view',
            'reports.export',
            'reports.print',
            'reports.view',
            'restaurant.bill.adjust',
            'restaurant.cancel',
            'restaurant.checkout',
            'restaurant.kitchen.send',
            'restaurant.kitchen.status.update',
            'restaurant.kitchen_ticket.print',
            'restaurant.line.add',
            'restaurant.order',
            'restaurant.order.update',
            'restaurant.payment.record',
            'restaurant.print',
            'restaurant.receipt.print',
            'restaurant.session.open',
            'restaurant.use',
            'restaurant.view',
            'sales_invoices.approve',
            'sales_invoices.cancel',
            'sales_invoices.create',
            'sales_invoices.delete',
            'sales_invoices.export',
            'sales_invoices.print',
            'sales_invoices.update',
            'sales_invoices.view',
            'sales_returns.approve',
            'sales_returns.cancel',
            'sales_returns.create',
            'sales_returns.delete',
            'sales_returns.export',
            'sales_returns.print',
            'sales_returns.update',
            'sales_returns.view',
            'settings.view',
            'suppliers.create',
            'suppliers.delete',
            'suppliers.export',
            'suppliers.print',
            'suppliers.update',
            'suppliers.view',
            'users.view',
            'vouchers.approve',
            'vouchers.cancel',
            'vouchers.create',
            'vouchers.delete',
            'vouchers.export',
            'vouchers.print',
            'vouchers.update',
            'vouchers.view',
            'warehouse_transfers.cancel',
            'warehouse_transfers.create',
            'warehouse_transfers.export',
            'warehouse_transfers.print',
            'warehouse_transfers.update',
            'warehouse_transfers.view',
            'warehouses.create',
            'warehouses.delete',
            'warehouses.export',
            'warehouses.print',
            'warehouses.update',
            'warehouses.view',
        ),
        'accountant': (
            'bank_accounts.create',
            'bank_accounts.delete',
            'bank_accounts.update',
            'bank_accounts.view',
            'branches.view',
            'cashboxes.create',
            'cashboxes.delete',
            'cashboxes.update',
            'cashboxes.view',
            'categories.view',
            'customers.create',
            'customers.delete',
            'customers.export',
            'customers.print',
            'customers.update',
            'customers.view',
            'expenses.cancel',
            'expenses.create',
            'expenses.delete',
            'expenses.export',
            'expenses.print',
            'expenses.update',
            'expenses.view',
            'items.export',
            'items.print',
            'items.view',
            'manufacturing.bom.export',
            'manufacturing.bom.print',
            'manufacturing.bom.view',
            'manufacturing.production_orders.export',
            'manufacturing.production_orders.print',
            'manufacturing.production_orders.view',
            'pos.print',
            'pos.receipt.print',
            'pos.view',
            'purchase_invoices.approve',
            'purchase_invoices.cancel',
            'purchase_invoices.create',
            'purchase_invoices.delete',
            'purchase_invoices.export',
            'purchase_invoices.print',
            'purchase_invoices.update',
            'purchase_invoices.view',
            'purchase_returns.approve',
            'purchase_returns.cancel',
            'purchase_returns.create',
            'purchase_returns.delete',
            'purchase_returns.export',
            'purchase_returns.print',
            'purchase_returns.update',
            'purchase_returns.view',
            'reports.export',
            'reports.print',
            'reports.view',
            'restaurant.kitchen_ticket.print',
            'restaurant.print',
            'restaurant.receipt.print',
            'restaurant.view',
            'sales_invoices.export',
            'sales_invoices.print',
            'sales_invoices.view',
            'sales_returns.export',
            'sales_returns.print',
            'sales_returns.view',
            'settings.export',
            'settings.view',
            'suppliers.create',
            'suppliers.delete',
            'suppliers.export',
            'suppliers.print',
            'suppliers.update',
            'suppliers.view',
            'users.view',
            'vouchers.approve',
            'vouchers.cancel',
            'vouchers.create',
            'vouchers.delete',
            'vouchers.export',
            'vouchers.print',
            'vouchers.update',
            'vouchers.view',
            'warehouse_transfers.export',
            'warehouse_transfers.print',
            'warehouse_transfers.view',
            'warehouses.export',
            'warehouses.print',
            'warehouses.view',
        ),
        'cashier': (
            'customers.create',
            'customers.delete',
            'customers.export',
            'customers.print',
            'customers.update',
            'customers.view',
            'items.print',
            'items.view',
            'pos.cart.clear',
            'pos.checkout',
            'pos.line.remove',
            'pos.print',
            'pos.receipt.print',
            'pos.resume',
            'pos.shift.close',
            'pos.shift.open',
            'pos.suspend',
            'pos.use',
            'pos.view',
            'pos.void',
            'restaurant.bill.adjust',
            'restaurant.cancel',
            'restaurant.checkout',
            'restaurant.kitchen.send',
            'restaurant.kitchen.status.update',
            'restaurant.kitchen_ticket.print',
            'restaurant.line.add',
            'restaurant.order',
            'restaurant.order.update',
            'restaurant.payment.record',
            'restaurant.print',
            'restaurant.receipt.print',
            'restaurant.session.open',
            'restaurant.use',
            'restaurant.view',
            'sales_invoices.approve',
            'sales_invoices.cancel',
            'sales_invoices.create',
            'sales_invoices.delete',
            'sales_invoices.export',
            'sales_invoices.print',
            'sales_invoices.update',
            'sales_invoices.view',
            'sales_returns.approve',
            'sales_returns.cancel',
            'sales_returns.create',
            'sales_returns.delete',
            'sales_returns.export',
            'sales_returns.print',
            'sales_returns.update',
            'sales_returns.view',
            'suppliers.create',
            'suppliers.delete',
            'suppliers.export',
            'suppliers.print',
            'suppliers.update',
            'suppliers.view',
            'warehouse_transfers.view',
            'warehouses.view',
        ),
        'viewer': (
            'bank_accounts.view',
            'branches.view',
            'cashboxes.view',
            'categories.view',
            'customers.view',
            'expenses.view',
            'items.view',
            'manufacturing.bom.view',
            'manufacturing.production_orders.view',
            'pos.view',
            'purchase_invoices.view',
            'purchase_returns.view',
            'reports.print',
            'reports.view',
            'restaurant.view',
            'sales_invoices.view',
            'sales_returns.view',
            'settings.view',
            'suppliers.view',
            'users.view',
            'vouchers.view',
            'warehouse_transfers.view',
            'warehouses.view',
        )
    }
    for role_name, permission_keys in role_permissions.items():
        for permission_key in permission_keys:
            cur.execute("""
                INSERT OR IGNORE INTO role_permissions(role_id, permission_key, allowed)
                SELECT r.id, ?, 1 FROM roles r
                WHERE r.name=? AND EXISTS (SELECT 1 FROM permissions p WHERE p.key=?)
            """, (permission_key, role_name, permission_key))
    conn.commit()

def migrate_phase264_audit_contract_columns(conn):
    """Phase 264: structured audit trail metadata used by shell contracts."""
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(audit_log)")
    cols = {row[1] for row in cur.fetchall()}
    for col_name, col_type in [
        ('audit_scope', 'TEXT'),
        ('permission_key', 'TEXT'),
        ('branch_id', 'INTEGER'),
        ('event_category', 'TEXT'),
    ]:
        if col_name not in cols:
            cur.execute(f"ALTER TABLE audit_log ADD COLUMN {col_name} {col_type}")
            cols.add(col_name)
    for sql in [
        'CREATE INDEX IF NOT EXISTS idx_audit_log_scope ON audit_log(audit_scope);',
        'CREATE INDEX IF NOT EXISTS idx_audit_log_permission ON audit_log(permission_key);',
        'CREATE INDEX IF NOT EXISTS idx_audit_log_branch ON audit_log(branch_id);',
        'CREATE INDEX IF NOT EXISTS idx_audit_log_category ON audit_log(event_category);',
    ]:
        try:
            cur.execute(sql)
        except Exception:
            pass
    conn.commit()


def ensure_db():
    # init_database uses CREATE IF NOT EXISTS and safe ALTERs, so running it
    # every startup also upgrades existing databases.
    init_database()




def migrate_phase205_category_permissions(conn):
    cur = conn.cursor()
    rows = [
        ('categories.view','categories','view','View categories'),
        ('categories.create','categories','create','Create categories'),
        ('categories.edit','categories','edit','Edit categories'),
        ('categories.archive','categories','archive','Archive categories'),
        ('categories.restore','categories','restore','Restore categories'),
    ]
    cur.executemany("INSERT OR IGNORE INTO permissions(key,module,action,description) VALUES (?,?,?,?)", rows)
    conn.commit()
