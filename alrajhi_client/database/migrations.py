# -*- coding: utf-8 -*-
import sqlite3
import os
import datetime
from .connection import DatabaseConnection, DB_PATH
from auth.password import hash_password

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
            FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            type TEXT,
            customer_id INTEGER,
            supplier_id INTEGER,
            date TEXT,
            reference TEXT,
            notes TEXT,
            total TEXT DEFAULT '0',
            paid TEXT DEFAULT '0',
            status TEXT,
            deleted_at TEXT,
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
            quantity_in_base TEXT DEFAULT '0',
            unit_cost TEXT DEFAULT '0',
            cost_amount TEXT DEFAULT '0',
            production_order_id INTEGER,
            conversion_factor REAL DEFAULT 1.0,
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

        CREATE TABLE IF NOT EXISTS material_reservations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            item_id INTEGER NOT NULL,
            reserved_qty TEXT NOT NULL,
            consumed_qty TEXT DEFAULT '0',
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
            value TEXT
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

    # ========== الفهارس ==========
    cursor.executescript('''

        CREATE INDEX IF NOT EXISTS idx_wh_user ON warehouses(user_id);
        CREATE INDEX IF NOT EXISTS idx_wh_bal_item ON item_warehouse_balances(item_id);
        CREATE INDEX IF NOT EXISTS idx_wh_bal_wh ON item_warehouse_balances(warehouse_id);
        CREATE INDEX IF NOT EXISTS idx_wh_mov_item ON warehouse_movements(item_id);
        CREATE INDEX IF NOT EXISTS idx_wh_mov_wh ON warehouse_movements(warehouse_id);
        CREATE INDEX IF NOT EXISTS idx_cashboxes_user_branch ON cashboxes(user_id, branch_id);
        CREATE INDEX IF NOT EXISTS idx_banks_user_branch ON bank_accounts(user_id, branch_id);
        CREATE INDEX IF NOT EXISTS idx_cash_mov_ref ON cash_bank_movements(reference_type, reference_id);
        CREATE INDEX IF NOT EXISTS idx_pos_shifts_user_status ON pos_shifts(user_id, status);
        CREATE INDEX IF NOT EXISTS idx_pos_shifts_cashbox ON pos_shifts(cashbox_id);
        CREATE INDEX IF NOT EXISTS idx_items_barcode ON items(barcode) WHERE barcode IS NOT NULL;
        CREATE INDEX IF NOT EXISTS idx_invoices_user_id ON invoices(user_id);
        CREATE INDEX IF NOT EXISTS idx_invoices_date ON invoices(date);
        CREATE INDEX IF NOT EXISTS idx_production_orders_product_id ON production_orders(product_id);
        CREATE INDEX IF NOT EXISTS idx_bom_product_id ON bom(product_id);
        CREATE INDEX IF NOT EXISTS idx_audit_log_user ON audit_log(user_id);
        CREATE INDEX IF NOT EXISTS idx_audit_log_timestamp ON audit_log(timestamp);
        CREATE INDEX IF NOT EXISTS idx_audit_log_entity ON audit_log(entity_type, entity_id);
        CREATE INDEX IF NOT EXISTS idx_audit_log_action ON audit_log(action);
        CREATE INDEX IF NOT EXISTS idx_exch_rate_hist_currency_date ON exchange_rate_history(currency_code, effective_date);
        CREATE INDEX IF NOT EXISTS idx_material_reservations_order ON material_reservations(order_id);
        CREATE INDEX IF NOT EXISTS idx_material_reservations_item ON material_reservations(item_id);
    ''')

    # ========== الإعدادات الافتراضية ==========
    cursor.executescript('''
        INSERT OR IGNORE INTO settings (key, value) VALUES ('currency_decimals', '2');
        INSERT OR IGNORE INTO settings (key, value) VALUES ('number_format', 'western');
        INSERT OR IGNORE INTO settings (key, value) VALUES ('language', 'ar');
        INSERT OR IGNORE INTO settings (key, value) VALUES ('theme', 'light');
        INSERT OR IGNORE INTO settings (key, value) VALUES ('base_currency', 'USD');
        INSERT OR IGNORE INTO settings (key, value) VALUES ('display_currency', 'SYP');
        INSERT OR IGNORE INTO settings (key, value) VALUES ('abbreviate_numbers', 'false');
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

    conn.executescript("""
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
    """)
    ''')

    conn.commit()
    conn.close()
    print(f"✅ تم تهيئة قاعدة البيانات المحلية في: {DB_PATH}")

def ensure_db():
    db = DatabaseConnection()
    if db.is_remote():
        return
    if not os.path.exists(DB_PATH):
        init_database()
    else:
        # ترقية الجداول القديمة (إضافة أعمدة جديدة)
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

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

        cursor.execute("PRAGMA table_info(invoice_lines)")
        columns = [col[1] for col in cursor.fetchall()]
        if 'conversion_factor' not in columns:
            cursor.execute("ALTER TABLE invoice_lines ADD COLUMN conversion_factor REAL DEFAULT 1.0")
            cursor.execute("UPDATE invoice_lines SET conversion_factor = 1.0 WHERE conversion_factor IS NULL")

        # التحقق من وجود عمودي linked_entry_id و linked_entry_type في production_orders
        cursor.execute("PRAGMA table_info(production_orders)")
        pcols = [col[1] for col in cursor.fetchall()]
        if 'linked_entry_id' not in pcols:
            cursor.execute("ALTER TABLE production_orders ADD COLUMN linked_entry_id INTEGER")
        if 'linked_entry_type' not in pcols:
            cursor.execute("ALTER TABLE production_orders ADD COLUMN linked_entry_type TEXT")

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
        cursor.execute("PRAGMA table_info(invoices)")
        incols = [col[1] for col in cursor.fetchall()]
        if 'exchange_rate_to_usd' not in incols:
            cursor.execute("ALTER TABLE invoices ADD COLUMN exchange_rate_to_usd REAL DEFAULT 1.0")
        if 'original_currency' not in incols:
            cursor.execute("ALTER TABLE invoices ADD COLUMN original_currency TEXT DEFAULT 'USD'")

        cursor.execute("PRAGMA table_info(vouchers)")
        vcols = [col[1] for col in cursor.fetchall()]
        if 'exchange_rate_to_usd' not in vcols:
            cursor.execute("ALTER TABLE vouchers ADD COLUMN exchange_rate_to_usd REAL DEFAULT 1.0")
        if 'original_currency' not in vcols:
            cursor.execute("ALTER TABLE vouchers ADD COLUMN original_currency TEXT DEFAULT 'USD'")

        cursor.execute("PRAGMA table_info(expenses)")
        ecols = [col[1] for col in cursor.fetchall()]
        if 'exchange_rate_to_usd' not in ecols:
            cursor.execute("ALTER TABLE expenses ADD COLUMN exchange_rate_to_usd REAL DEFAULT 1.0")
        if 'original_currency' not in ecols:
            cursor.execute("ALTER TABLE expenses ADD COLUMN original_currency TEXT DEFAULT 'USD'")


        # Warehouse-4: production order warehouse links
        try:
            cursor.execute("PRAGMA table_info(production_orders)")
            _po_cols = {row[1] for row in cursor.fetchall()}
            if 'raw_warehouse_id' not in _po_cols:
                cursor.execute("ALTER TABLE production_orders ADD COLUMN raw_warehouse_id INTEGER")
            if 'output_warehouse_id' not in _po_cols:
                cursor.execute("ALTER TABLE production_orders ADD COLUMN output_warehouse_id INTEGER")
        except Exception:
            pass
        
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

    conn.commit()
    conn.close()


