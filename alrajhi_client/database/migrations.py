# -*- coding: utf-8 -*-
import sqlite3
import os
import datetime
from .connection import DatabaseConnection, DB_PATH
from auth.password import hash_password
from .schema_manager import apply_common_schema

def init_database():
    db = DatabaseConnection()
    if db.is_remote():
        print("⚠️ وضع العميل: قاعدة البيانات على الخادم، لا حاجة لإنشاء محلي.")
        return

    db.close()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys=ON')
    cursor = conn.cursor()

    # ========== جداول الراجحي الأساسية ==========
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
            cashbox_id INTEGER,
            bank_account_id INTEGER,
            payment_method TEXT DEFAULT 'cash',
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
            unit_id INTEGER,
            conversion_factor REAL DEFAULT 1.0,
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
            cashbox_id INTEGER,
            bank_account_id INTEGER,
            payment_method TEXT DEFAULT 'cash',
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
            cashbox_id INTEGER,
            bank_account_id INTEGER,
            payment_method TEXT DEFAULT 'cash',
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



        CREATE TABLE IF NOT EXISTS cashboxes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            branch_id INTEGER,
            name TEXT NOT NULL,
            code TEXT,
            notes TEXT,
            is_default INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            deleted_at TEXT,
            created_at TEXT,
            updated_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (branch_id) REFERENCES branches(id),
            UNIQUE(user_id, branch_id, name),
            UNIQUE(user_id, code)
        );

        CREATE TABLE IF NOT EXISTS bank_accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            branch_id INTEGER,
            bank_name TEXT NOT NULL,
            account_name TEXT,
            account_number TEXT,
            iban TEXT,
            notes TEXT,
            is_active INTEGER DEFAULT 1,
            deleted_at TEXT,
            created_at TEXT,
            updated_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (branch_id) REFERENCES branches(id)
        );

        CREATE TABLE IF NOT EXISTS cash_bank_movements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            branch_id INTEGER,
            cashbox_id INTEGER,
            bank_account_id INTEGER,
            movement_type TEXT NOT NULL,
            amount TEXT NOT NULL,
            direction TEXT,
            reference_type TEXT,
            reference_id INTEGER,
            description TEXT,
            movement_date TEXT,
            created_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (branch_id) REFERENCES branches(id),
            FOREIGN KEY (cashbox_id) REFERENCES cashboxes(id),
            FOREIGN KEY (bank_account_id) REFERENCES bank_accounts(id)
        );


        CREATE TABLE IF NOT EXISTS pos_shifts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            branch_id INTEGER,
            cashbox_id INTEGER NOT NULL,
            opening_amount TEXT DEFAULT '0',
            closing_amount TEXT,
            expected_amount TEXT DEFAULT '0',
            actual_amount TEXT,
            difference_amount TEXT,
            total_sales TEXT DEFAULT '0',
            total_cash TEXT DEFAULT '0',
            total_card TEXT DEFAULT '0',
            status TEXT DEFAULT 'open',
            opened_at TEXT,
            closed_at TEXT,
            notes TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (branch_id) REFERENCES branches(id),
            FOREIGN KEY (cashbox_id) REFERENCES cashboxes(id)
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
            linked_entry_id INTEGER,
            linked_entry_type TEXT,
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

        CREATE TABLE IF NOT EXISTS material_reservations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            item_id INTEGER NOT NULL,
            reserved_qty TEXT NOT NULL,
            consumed_qty TEXT DEFAULT '0',
            unit_id INTEGER,
            unit_name TEXT,
            conversion_factor TEXT DEFAULT '1',
            reserved_base_qty TEXT DEFAULT '0',
            consumed_base_qty TEXT DEFAULT '0',
            barcode_scope TEXT,
            FOREIGN KEY (order_id) REFERENCES production_orders(id) ON DELETE CASCADE,
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

        CREATE TABLE IF NOT EXISTS settings_audit (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            setting_key TEXT NOT NULL,
            old_value TEXT,
            new_value TEXT,
            changed_by TEXT,
            changed_at TEXT NOT NULL,
            source TEXT DEFAULT 'SettingsService'
        );

        CREATE INDEX IF NOT EXISTS idx_settings_audit_key_time
            ON settings_audit(setting_key, changed_at);

        CREATE TABLE IF NOT EXISTS security_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT NOT NULL,
            action TEXT,
            role TEXT,
            username TEXT,
            allowed INTEGER NOT NULL DEFAULT 0,
            reason TEXT,
            context TEXT,
            created_at TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_security_events_time
            ON security_events(created_at);

        CREATE INDEX IF NOT EXISTS idx_security_events_action
            ON security_events(action, role);


        CREATE TABLE IF NOT EXISTS settings_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT,
            is_active INTEGER NOT NULL DEFAULT 0,
            created_at TEXT,
            updated_at TEXT
        );

        CREATE TABLE IF NOT EXISTS settings_profile_values (
            profile_id INTEGER NOT NULL,
            setting_key TEXT NOT NULL,
            setting_value TEXT,
            updated_at TEXT,
            PRIMARY KEY (profile_id, setting_key),
            FOREIGN KEY(profile_id) REFERENCES settings_profiles(id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_settings_profile_values_key
            ON settings_profile_values(setting_key);

        INSERT OR IGNORE INTO settings_profiles(id, name, description, is_active, created_at, updated_at)
            VALUES (1, 'Default', 'ملف الإعدادات الافتراضي', 1, datetime('now'), datetime('now'));

        UPDATE settings_profiles
            SET is_active = CASE WHEN id = (SELECT COALESCE(MIN(id), 1) FROM settings_profiles WHERE is_active = 1) THEN 1 ELSE 0 END
            WHERE EXISTS (SELECT 1 FROM settings_profiles WHERE is_active = 1);

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
        CREATE INDEX IF NOT EXISTS idx_workflow_events_entity
            ON workflow_events(entity_type, entity_id, created_at);
        -- Phase151 hotfix: this index is created after safe ALTER migrations.
        -- Creating it here breaks upgraded databases whose invoices table existed
        -- before workflow_status was added.

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

    
    cursor.execute("PRAGMA table_info(settings)")
    settings_columns = [row[1] for row in cursor.fetchall()]
    if 'category' not in settings_columns:
        cursor.execute("ALTER TABLE settings ADD COLUMN category TEXT")
    if 'updated_at' not in settings_columns:
        cursor.execute("ALTER TABLE settings ADD COLUMN updated_at TEXT")

    # Production-readiness: normalize legacy columns before indexes/default data.
    apply_common_schema(conn)

    # ========== الفهارس ==========
    for _idx_sql in [
        'CREATE INDEX IF NOT EXISTS idx_wh_user ON warehouses(user_id);',
        'CREATE INDEX IF NOT EXISTS idx_wh_bal_item ON item_warehouse_balances(item_id);',
        'CREATE INDEX IF NOT EXISTS idx_wh_bal_wh ON item_warehouse_balances(warehouse_id);',
        'CREATE INDEX IF NOT EXISTS idx_wh_mov_item ON warehouse_movements(item_id);',
        'CREATE INDEX IF NOT EXISTS idx_wh_mov_wh ON warehouse_movements(warehouse_id);',
        'CREATE INDEX IF NOT EXISTS idx_cashboxes_user_branch ON cashboxes(user_id, branch_id);',
        'CREATE INDEX IF NOT EXISTS idx_banks_user_branch ON bank_accounts(user_id, branch_id);',
        'CREATE INDEX IF NOT EXISTS idx_cash_mov_ref ON cash_bank_movements(reference_type, reference_id);',
        'CREATE INDEX IF NOT EXISTS idx_pos_shifts_user_status ON pos_shifts(user_id, status);',
        'CREATE INDEX IF NOT EXISTS idx_pos_shifts_cashbox ON pos_shifts(cashbox_id);',
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
        'CREATE INDEX IF NOT EXISTS idx_exch_rate_hist_currency_date ON exchange_rate_history(currency_code, effective_date);',
        'CREATE INDEX IF NOT EXISTS idx_material_reservations_order ON material_reservations(order_id);',
        'CREATE INDEX IF NOT EXISTS idx_material_reservations_item ON material_reservations(item_id);'
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

    # ========== الإعدادات الافتراضية ==========
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

    # ========== مستخدم admin افتراضي ==========
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

    # ========== أسعار الصرف الافتراضية ==========
    now = datetime.datetime.now().isoformat()
    default_rates = [
        ('USD', 1.0), ('SAR', 3.75), ('SYP', 14000.0), ('EUR', 0.92),
        ('GBP', 0.79), ('AED', 3.67), ('QAR', 3.64), ('KWD', 0.31), ('OMR', 0.38),
    ]
    for code, rate in default_rates:
        cursor.execute("INSERT OR IGNORE INTO exchange_rates (currency_code, rate_to_usd, updated_at) VALUES (?,?,?)",
                       (code, rate, now))


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
            unit_id INTEGER,
            conversion_factor REAL DEFAULT 1.0,
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
            unit_id INTEGER,
            conversion_factor REAL DEFAULT 1.0,
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

    # Phase151 hotfix: init_database() is also called for existing SQLite files.
    # CREATE TABLE IF NOT EXISTS does not add new columns to an existing table;
    # therefore every workflow column must be ensured before creating indexes
    # that reference it.
    def _table_exists_init(name):
        cursor.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND lower(name)=lower(?) LIMIT 1", (name,))
        return cursor.fetchone() is not None

    def _columns_init(name):
        if not _table_exists_init(name):
            return set()
        cursor.execute(f"PRAGMA table_info({name})")
        return {row[1] for row in cursor.fetchall()}

    if _table_exists_init('invoices'):
        invoice_columns = _columns_init('invoices')
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
        if _table_exists_init('invoices') and 'workflow_status' in _columns_init('invoices'):
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_invoices_workflow_status ON invoices(workflow_status)")


    # Phase157: Enterprise RBAC tables also during first database initialization

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
        CREATE TABLE IF NOT EXISTS roles (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE NOT NULL, display_name TEXT, description TEXT, is_system INTEGER DEFAULT 0, is_active INTEGER DEFAULT 1, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS permissions (key TEXT PRIMARY KEY, module TEXT NOT NULL, action TEXT NOT NULL, description TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS role_permissions (role_id INTEGER NOT NULL, permission_key TEXT NOT NULL, allowed INTEGER NOT NULL DEFAULT 1, created_at TEXT DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY(role_id, permission_key), FOREIGN KEY(role_id) REFERENCES roles(id) ON DELETE CASCADE, FOREIGN KEY(permission_key) REFERENCES permissions(key) ON DELETE CASCADE);
        CREATE TABLE IF NOT EXISTS user_roles (user_id TEXT NOT NULL, role_id INTEGER NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY(user_id, role_id), FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE, FOREIGN KEY(role_id) REFERENCES roles(id) ON DELETE CASCADE);
        CREATE TABLE IF NOT EXISTS user_branch_access (user_id TEXT NOT NULL, branch_id INTEGER NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY(user_id, branch_id), FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE, FOREIGN KEY(branch_id) REFERENCES branches(id) ON DELETE CASCADE);
        CREATE INDEX IF NOT EXISTS idx_user_roles_user ON user_roles(user_id);
        CREATE INDEX IF NOT EXISTS idx_role_permissions_role ON role_permissions(role_id);
        CREATE INDEX IF NOT EXISTS idx_user_branch_access_user ON user_branch_access(user_id);
        INSERT OR IGNORE INTO roles(name, display_name, description, is_system) VALUES ('admin','Administrator / مدير النظام','Full system access',1),('manager','Manager / مدير','Operational management access',1),('accountant','Accountant / محاسب','Accounting and financial reporting access',1),('cashier','Cashier / أمين صندوق','Sales and cashbox access',1),('viewer','Viewer / مشاهدة','Read-only access',1);
        INSERT OR IGNORE INTO permissions(key,module,action,description) VALUES ('reports.view','reports','view','View reports'),('reports.export','reports','export','Export reports'),('invoices.edit','invoices','edit','Edit invoices'),('invoices.delete','invoices','delete','Delete invoices'),('returns.edit','returns','edit','Edit returns'),('branches.view_all','branches','view_all','View all branches'),('branches.manage_all','branches','manage_all','Manage all branches'),('approval.submit','approval','submit','Submit documents for approval'),('approval.approve','approval','approve','Approve documents'),('approval.reject','approval','reject','Reject approval requests'),('accounting.view','accounting','view','View accounting reports'),('accounting.post','accounting','post','Post journal entries / documents'),('accounting.close_period','accounting','close_period','Close accounting periods'),('settings.manage','settings','manage','Manage system settings'),('users.manage','users','manage','Manage users and roles');
        INSERT OR IGNORE INTO role_permissions(role_id, permission_key, allowed) SELECT r.id, p.key, 1 FROM roles r CROSS JOIN permissions p WHERE r.name='admin';
        INSERT OR IGNORE INTO role_permissions(role_id, permission_key, allowed) SELECT r.id, p.key, 1 FROM roles r JOIN permissions p ON p.key IN ('reports.view','reports.export','invoices.edit','returns.edit','branches.view_all','approval.submit','approval.approve','approval.reject') WHERE r.name='manager';
        INSERT OR IGNORE INTO role_permissions(role_id, permission_key, allowed) SELECT r.id, p.key, 1 FROM roles r JOIN permissions p ON p.key IN ('reports.view','reports.export','accounting.view','accounting.post','accounting.close_period','approval.submit') WHERE r.name='accountant';
        INSERT OR IGNORE INTO role_permissions(role_id, permission_key, allowed) SELECT r.id, p.key, 1 FROM roles r JOIN permissions p ON p.key IN ('approval.submit') WHERE r.name='cashier';
        INSERT OR IGNORE INTO role_permissions(role_id, permission_key, allowed) SELECT r.id, p.key, 1 FROM roles r JOIN permissions p ON p.key IN ('reports.view') WHERE r.name='viewer';
        INSERT OR IGNORE INTO user_roles(user_id, role_id) SELECT u.id, r.id FROM users u JOIN roles r ON lower(COALESCE(u.role,'user')) = r.name;
    """)

    apply_common_schema(conn)
    _phase158_159_schema(conn)
    conn.commit()
    conn.close()
    print(f"✅ تم تهيئة قاعدة البيانات المحلية في: {DB_PATH}")


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


def ensure_db():
    db = DatabaseConnection()
    if db.is_remote():
        return
    if not os.path.exists(DB_PATH):
        init_database()
        return
    else:
        # Phase128: bootstrap core schema before applying legacy ALTER migrations.
        # Some restored/old databases may exist as files but miss core tables such as
        # invoice_lines or production_orders; ALTER TABLE must never run before the
        # base CREATE TABLE IF NOT EXISTS script has had a chance to create them.
        init_database()
        # ترقية الجداول القديمة (إضافة أعمدة جديدة)
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

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
            INSERT OR IGNORE INTO accounts(code, name, type) VALUES ('4000','Sales Revenue / إيرادات المبيعات','REVENUE');
            INSERT OR IGNORE INTO accounts(code, name, type) VALUES ('5000','Purchases / مشتريات','EXPENSE');
            INSERT OR IGNORE INTO settings (key, value, category) VALUES ('approval/non_admin_can_approve', 'false', 'approval');
        """)

        apply_common_schema(conn)

        def _table_exists(name):
            cursor.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND lower(name)=lower(?) LIMIT 1", (name,))
            return cursor.fetchone() is not None

        def _columns(name):
            if not _table_exists(name):
                return set()
            cursor.execute(f"PRAGMA table_info({name})")
            return {row[1] for row in cursor.fetchall()}

        def _add_column_if_missing(table, column, ddl_tail):
            if not _table_exists(table):
                return False
            cols = _columns(table)
            if column not in cols:
                cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {ddl_tail}")
                return True
            return False

        # Phase151 workflow lifecycle columns for upgraded databases
        for col_name, col_type in [
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
            _add_column_if_missing('invoices', col_name, col_type)
        cursor.execute("""
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
            )
        """)
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_workflow_events_entity ON workflow_events(entity_type, entity_id, created_at)')
        if 'workflow_status' in [row[1] for row in cursor.execute("PRAGMA table_info(invoices)").fetchall()]:
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_invoices_workflow_status ON invoices(workflow_status)')


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
            INSERT OR IGNORE INTO accounts(code, name, type) VALUES ('4000','Sales Revenue / إيرادات المبيعات','REVENUE');
            INSERT OR IGNORE INTO accounts(code, name, type) VALUES ('5000','Purchases / مشتريات','EXPENSE');
            INSERT OR IGNORE INTO settings (key, value, category) VALUES ('approval/non_admin_can_approve', 'false', 'approval');
        """)

        # Ensure category hierarchy/status support exists for upgraded databases
        cursor.execute("PRAGMA table_info(categories)")
        category_columns = [col[1] for col in cursor.fetchall()]
        for col_name, col_type in [
            ('parent_id', 'INTEGER'),
            ('description', 'TEXT'),
            ('color', "TEXT DEFAULT '#64748B'"),
            ('icon', "TEXT DEFAULT 'folder'"),
            ('is_active', 'INTEGER DEFAULT 1'),
            ('deleted_at', 'TEXT'),
        ]:
            if col_name not in category_columns:
                cursor.execute(f"ALTER TABLE categories ADD COLUMN {col_name} {col_type}")
        cursor.execute("UPDATE categories SET is_active = 1 WHERE is_active IS NULL")



        # Warehouse-1 core tables and default migration
        cursor.executescript('''
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
                unit_cost TEXT DEFAULT '0',
                notes TEXT,
                status TEXT DEFAULT 'active',
                created_at TEXT,
                cancelled_at TEXT,
                UNIQUE(user_id, transfer_no)
            );
            CREATE INDEX IF NOT EXISTS idx_wh_user ON warehouses(user_id);
            CREATE INDEX IF NOT EXISTS idx_wh_bal_item ON item_warehouse_balances(item_id);
            CREATE INDEX IF NOT EXISTS idx_wh_bal_wh ON item_warehouse_balances(warehouse_id);
            CREATE INDEX IF NOT EXISTS idx_wh_mov_item ON warehouse_movements(item_id);
            CREATE INDEX IF NOT EXISTS idx_wh_mov_wh ON warehouse_movements(warehouse_id);

            -- Branch/Cashbox/Bank tables are created here in the upgrade path too.
            -- Previously only their indexes were created here, which made existing
            -- databases fail with: no such table: main.cashboxes.
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

            CREATE TABLE IF NOT EXISTS cashboxes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                branch_id INTEGER,
                name TEXT NOT NULL,
                code TEXT,
                notes TEXT,
                is_default INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                deleted_at TEXT,
                created_at TEXT,
                updated_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (branch_id) REFERENCES branches(id),
                UNIQUE(user_id, branch_id, name),
                UNIQUE(user_id, code)
            );

            CREATE TABLE IF NOT EXISTS bank_accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                branch_id INTEGER,
                bank_name TEXT NOT NULL,
                account_name TEXT,
                account_number TEXT,
                iban TEXT,
                notes TEXT,
                is_active INTEGER DEFAULT 1,
                deleted_at TEXT,
                created_at TEXT,
                updated_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (branch_id) REFERENCES branches(id)
            );

            CREATE TABLE IF NOT EXISTS cash_bank_movements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                branch_id INTEGER,
                cashbox_id INTEGER,
                bank_account_id INTEGER,
                movement_type TEXT NOT NULL,
                amount TEXT NOT NULL,
                direction TEXT,
                reference_type TEXT,
                reference_id INTEGER,
                description TEXT,
                movement_date TEXT,
                created_at TEXT,
                shift_id INTEGER,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (branch_id) REFERENCES branches(id),
                FOREIGN KEY (cashbox_id) REFERENCES cashboxes(id),
                FOREIGN KEY (bank_account_id) REFERENCES bank_accounts(id)
            );

            CREATE TABLE IF NOT EXISTS pos_shifts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                branch_id INTEGER,
                cashbox_id INTEGER NOT NULL,
                opening_amount TEXT DEFAULT '0',
                closing_amount TEXT,
                expected_amount TEXT DEFAULT '0',
                actual_amount TEXT,
                difference_amount TEXT,
                total_sales TEXT DEFAULT '0',
                total_cash TEXT DEFAULT '0',
                total_card TEXT DEFAULT '0',
                status TEXT DEFAULT 'open',
                opened_at TEXT,
                closed_at TEXT,
                notes TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (branch_id) REFERENCES branches(id),
                FOREIGN KEY (cashbox_id) REFERENCES cashboxes(id)
            );

            CREATE INDEX IF NOT EXISTS idx_cashboxes_user_branch ON cashboxes(user_id, branch_id);
            CREATE INDEX IF NOT EXISTS idx_banks_user_branch ON bank_accounts(user_id, branch_id);
            CREATE INDEX IF NOT EXISTS idx_cash_mov_ref ON cash_bank_movements(reference_type, reference_id);
            CREATE INDEX IF NOT EXISTS idx_pos_shifts_user_status ON pos_shifts(user_id, status);
            CREATE INDEX IF NOT EXISTS idx_pos_shifts_cashbox ON pos_shifts(cashbox_id);
        ''')
        now = datetime.datetime.now().isoformat()
        warehouse_users = cursor.execute('''
            SELECT id FROM users
            UNION
            SELECT DISTINCT user_id AS id FROM items WHERE user_id IS NOT NULL
        ''').fetchall()
        for wu in warehouse_users:
            uid = wu[0]
            wh = cursor.execute("SELECT id FROM warehouses WHERE user_id=? AND is_default=1 AND deleted_at IS NULL LIMIT 1", (uid,)).fetchone()
            if wh:
                wh_id = wh[0]
            else:
                cursor.execute('''
                    INSERT OR IGNORE INTO warehouses
                    (user_id, name, code, location, notes, is_default, is_active, created_at, updated_at)
                    VALUES (?, 'المستودع الرئيسي', 'MAIN', '', 'تم إنشاؤه تلقائياً عند تفعيل نظام المستودعات', 1, 1, ?, ?)
                ''', (uid, now, now))
                wh_id = cursor.execute("SELECT id FROM warehouses WHERE user_id=? AND name='المستودع الرئيسي' LIMIT 1", (uid,)).fetchone()[0]
            for item in cursor.execute("SELECT id, COALESCE(quantity, '0'), COALESCE(average_cost, '0') FROM items WHERE user_id=? AND deleted_at IS NULL", (uid,)).fetchall():
                if cursor.execute("SELECT id FROM item_warehouse_balances WHERE user_id=? AND item_id=? AND warehouse_id=?", (uid, item[0], wh_id)).fetchone():
                    continue
                cursor.execute('''
                    INSERT INTO item_warehouse_balances (user_id, item_id, warehouse_id, quantity, average_cost, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (uid, item[0], wh_id, item[1], item[2], now))
                try:
                    qty_nonzero = abs(float(item[1] or 0)) > 0.000001
                except Exception:
                    qty_nonzero = False
                if qty_nonzero:
                    cursor.execute('''
                        INSERT INTO warehouse_movements
                        (user_id, item_id, warehouse_id, movement_type, quantity, unit_cost, reference_type, notes, movement_date, created_at)
                        VALUES (?, ?, ?, 'migration_opening', ?, ?, 'migration', 'ترحيل رصيد المادة إلى المستودع الرئيسي', ?, ?)
                    ''', (uid, item[0], wh_id, item[1], item[2], now, now))

        # التحقق من وجود عمود conversion_factor في invoice_lines
        # Ensure item soft-delete support exists for upgraded databases
        cursor.execute("PRAGMA table_info(items)")
        item_columns = [col[1] for col in cursor.fetchall()]
        if 'deleted_at' not in item_columns:
            cursor.execute("ALTER TABLE items ADD COLUMN deleted_at TEXT")
        if 'reorder_level' not in item_columns:
            cursor.execute("ALTER TABLE items ADD COLUMN reorder_level TEXT DEFAULT '0'")

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND lower(name)=lower('invoice_lines')")
        if cursor.fetchone():
            cursor.execute("PRAGMA table_info(invoice_lines)")
            columns = [col[1] for col in cursor.fetchall()]
            if 'conversion_factor' not in columns:
                cursor.execute("ALTER TABLE invoice_lines ADD COLUMN conversion_factor REAL DEFAULT 1.0")
                cursor.execute("UPDATE invoice_lines SET conversion_factor = 1.0 WHERE conversion_factor IS NULL")
        else:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS invoice_lines (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    invoice_id INTEGER,
                    item_id INTEGER,
                    description TEXT,
                    quantity TEXT DEFAULT '0',
                    unit_price TEXT DEFAULT '0',
                    total TEXT DEFAULT '0',
                    unit TEXT,
                    unit_id INTEGER,
                    conversion_factor REAL DEFAULT 1.0,
                    quantity_in_base TEXT DEFAULT '0',
                    unit_cost TEXT DEFAULT '0',
                    cost_amount TEXT DEFAULT '0',
                    production_order_id INTEGER,
                    FOREIGN KEY (invoice_id) REFERENCES invoices(id) ON DELETE CASCADE,
                    FOREIGN KEY (item_id) REFERENCES items(id)
                )
            """)

        # التحقق من وجود عمودي linked_entry_id و linked_entry_type في production_orders
        _add_column_if_missing('production_orders', 'linked_entry_id', 'INTEGER')
        _add_column_if_missing('production_orders', 'linked_entry_type', 'TEXT')

        # جدول material_reservations
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='material_reservations'")
        if not cursor.fetchone():
            cursor.execute('''
                CREATE TABLE material_reservations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id INTEGER NOT NULL,
                    item_id INTEGER NOT NULL,
                    reserved_qty TEXT NOT NULL,
                    consumed_qty TEXT DEFAULT '0',
                    FOREIGN KEY (order_id) REFERENCES production_orders(id) ON DELETE CASCADE,
                    FOREIGN KEY (item_id) REFERENCES items(id)
                )
            ''')
            cursor.execute('CREATE INDEX idx_material_reservations_order ON material_reservations(order_id)')
            cursor.execute('CREATE INDEX idx_material_reservations_item ON material_reservations(item_id)')

        # جدول exchange_rate_history
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='exchange_rate_history'")
        if not cursor.fetchone():
            cursor.execute('''
                CREATE TABLE exchange_rate_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    currency_code TEXT NOT NULL,
                    rate_to_usd REAL NOT NULL,
                    effective_date TEXT NOT NULL,
                    created_at TEXT
                )
            ''')
            cursor.execute('CREATE INDEX idx_exch_rate_hist_currency_date ON exchange_rate_history(currency_code, effective_date)')

        # جدول audit_log
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='audit_log'")
        if not cursor.fetchone():
            cursor.execute('''
                CREATE TABLE audit_log (
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
                )
            ''')


        # توسيع audit_log للربط والتتبع التفصيلي مع التوافق الخلفي
        cursor.execute("PRAGMA table_info(audit_log)")
        audit_cols = [col[1] for col in cursor.fetchall()]
        for col_name, col_type in [
            ('event_time', 'TEXT'), ('entity_type', 'TEXT'), ('entity_id', 'INTEGER'),
            ('old_values', 'TEXT'), ('new_values', 'TEXT'), ('session_id', 'TEXT'), ('source', 'TEXT')
        ]:
            if col_name not in audit_cols:
                cursor.execute(f"ALTER TABLE audit_log ADD COLUMN {col_name} {col_type}")
        cursor.execute("UPDATE audit_log SET event_time = COALESCE(event_time, timestamp), entity_type = COALESCE(entity_type, table_name), entity_id = COALESCE(entity_id, record_id) WHERE event_time IS NULL OR entity_type IS NULL OR entity_id IS NULL")

        # جدول token_blacklist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='token_blacklist'")
        if not cursor.fetchone():
            cursor.execute('''
                CREATE TABLE token_blacklist (
                    jti TEXT PRIMARY KEY,
                    created_at TEXT
                )
            ''')

        # التأكد من وجود أعمدة exchange_rate_to_usd و original_currency في invoices, vouchers, expenses
        _add_column_if_missing('invoices', 'exchange_rate_to_usd', 'REAL DEFAULT 1.0')
        _add_column_if_missing('invoices', 'original_currency', "TEXT DEFAULT 'USD'")
        _add_column_if_missing('vouchers', 'exchange_rate_to_usd', 'REAL DEFAULT 1.0')
        _add_column_if_missing('vouchers', 'original_currency', "TEXT DEFAULT 'USD'")
        _add_column_if_missing('expenses', 'exchange_rate_to_usd', 'REAL DEFAULT 1.0')
        _add_column_if_missing('expenses', 'original_currency', "TEXT DEFAULT 'USD'")


        # Warehouse-4: production order warehouse links
        _add_column_if_missing('production_orders', 'raw_warehouse_id', 'INTEGER')
        _add_column_if_missing('production_orders', 'output_warehouse_id', 'INTEGER')
        
    # Branches core migration/bootstrap

        # Branches operational integration: users/invoices/vouchers/expenses
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
            unit_id INTEGER,
            conversion_factor REAL DEFAULT 1.0,
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


    # Phase155: ensure approval/accounting/financial-statement tables on first startup
    cursor.executescript('''
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
        CREATE TABLE IF NOT EXISTS accounting_periods (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, start_date TEXT NOT NULL, end_date TEXT NOT NULL, status TEXT DEFAULT 'OPEN', closed_at TEXT, closed_by TEXT, closing_entry_id INTEGER, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE INDEX IF NOT EXISTS idx_accounting_periods_dates ON accounting_periods(start_date, end_date, status);
        INSERT OR IGNORE INTO accounts(code,name,type) VALUES ('1000','Cash / صندوق','ASSET');
        INSERT OR IGNORE INTO accounts(code,name,type) VALUES ('1100','Accounts Receivable / ذمم العملاء','ASSET');
        INSERT OR IGNORE INTO accounts(code,name,type) VALUES ('1200','Inventory / مخزون','ASSET');
        INSERT OR IGNORE INTO accounts(code,name,type) VALUES ('2000','Accounts Payable / ذمم الموردين','LIABILITY');
        INSERT OR IGNORE INTO accounts(code,name,type) VALUES ('3000','Owner Equity / حقوق الملكية','EQUITY');
        INSERT OR IGNORE INTO accounts(code,name,type) VALUES ('3100','Retained Earnings / أرباح مرحلة','EQUITY');
        INSERT OR IGNORE INTO accounts(code,name,type) VALUES ('3900','Current Year Earnings / أرباح السنة الحالية','EQUITY');
        INSERT OR IGNORE INTO accounts(code,name,type) VALUES ('4000','Sales Revenue / إيرادات المبيعات','REVENUE');
        INSERT OR IGNORE INTO accounts(code,name,type) VALUES ('5000','Purchases / مشتريات','EXPENSE');
        INSERT OR IGNORE INTO accounts(code,name,type) VALUES ('5900','Closing Summary / ملخص الإقفال','EQUITY');
    ''')


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
