# -*- coding: utf-8 -*-
"""Schema guard for Alrajhi SQLite databases.

This module is intentionally small and idempotent. It is called by both the
client and server migration files so old databases are upgraded to the current
application schema before any INSERT/UPDATE statements run.
"""

SCHEMA_VERSION = 20260611

REQUIRED_COLUMNS = {
    "users": {
        "branch_id": "INTEGER",
        "cash_balance": "TEXT DEFAULT '0'",
        "force_password_change": "INTEGER DEFAULT 0",
    },
    "items": {
        "category_id": "INTEGER",
        "item_type": "TEXT",
        "average_cost": "TEXT DEFAULT '0'",
        "barcode": "TEXT",
        "reorder_level": "TEXT DEFAULT '0'",
        "deleted_at": "TEXT",
    },
    "categories": {
        "parent_id": "INTEGER",
        "description": "TEXT",
        "color": "TEXT DEFAULT '#64748B'",
        "icon": "TEXT DEFAULT 'folder'",
        "is_active": "INTEGER DEFAULT 1",
        "deleted_at": "TEXT",
    },
    "invoices": {
        "exchange_rate_to_usd": "REAL DEFAULT 1.0",
        "original_currency": "TEXT DEFAULT 'USD'",
        "warehouse_id": "INTEGER",
        "branch_id": "INTEGER",
        "cashbox_id": "INTEGER",
        "bank_account_id": "INTEGER",
        "payment_method": "TEXT DEFAULT 'cash'",
        "shift_id": "INTEGER",
        "workflow_status": "TEXT DEFAULT 'DRAFT'",
        "submitted_at": "TEXT",
        "submitted_by": "TEXT",
        "approved_at": "TEXT",
        "approved_by": "TEXT",
        "posted_at": "TEXT",
        "posted_by": "TEXT",
        "cancelled_at": "TEXT",
        "cancelled_by": "TEXT",
        "deleted_at": "TEXT",
        "deleted_by": "TEXT",
    },
    "invoice_lines": {
        "unit": "TEXT",
        "quantity_in_base": "TEXT DEFAULT '0'",
        "unit_cost": "TEXT DEFAULT '0'",
        "cost_amount": "TEXT DEFAULT '0'",
        "production_order_id": "INTEGER",
        "conversion_factor": "REAL DEFAULT 1.0",
    },
    "sales_return_lines": {
        "unit_id": "INTEGER",
        "conversion_factor": "REAL DEFAULT 1.0",
    },
    "purchase_return_lines": {
        "unit_id": "INTEGER",
        "conversion_factor": "REAL DEFAULT 1.0",
    },
    "inventory_movements": {
        "item_id": "INTEGER",
        "user_id": "TEXT",
        "movement_type": "TEXT",
        "quantity": "TEXT",
        "unit_cost": "TEXT",
        "reference_id": "INTEGER",
        "movement_date": "TEXT",
        "created_at": "TEXT DEFAULT CURRENT_TIMESTAMP",
    },
    "vouchers": {
        "exchange_rate_to_usd": "REAL DEFAULT 1.0",
        "original_currency": "TEXT DEFAULT 'USD'",
        "warehouse_id": "INTEGER",
        "branch_id": "INTEGER",
        "cashbox_id": "INTEGER",
        "bank_account_id": "INTEGER",
        "payment_method": "TEXT DEFAULT 'cash'",
    },
    "expenses": {
        "exchange_rate_to_usd": "REAL DEFAULT 1.0",
        "original_currency": "TEXT DEFAULT 'USD'",
        "warehouse_id": "INTEGER",
        "branch_id": "INTEGER",
        "cashbox_id": "INTEGER",
        "bank_account_id": "INTEGER",
        "payment_method": "TEXT DEFAULT 'cash'",
    },
    "warehouses": {
        "code": "TEXT",
        "location": "TEXT",
        "notes": "TEXT",
        "branch_id": "INTEGER",
        "is_default": "INTEGER DEFAULT 0",
        "is_active": "INTEGER DEFAULT 1",
        "deleted_at": "TEXT",
        "created_at": "TEXT",
        "updated_at": "TEXT",
    },
    "branches": {
        "code": "TEXT",
        "address": "TEXT",
        "phone": "TEXT",
        "notes": "TEXT",
        "is_default": "INTEGER DEFAULT 0",
        "is_active": "INTEGER DEFAULT 1",
        "deleted_at": "TEXT",
        "created_at": "TEXT",
        "updated_at": "TEXT",
    },
    "cash_bank_movements": {
        "branch_id": "INTEGER",
        "cashbox_id": "INTEGER",
        "bank_account_id": "INTEGER",
        "direction": "TEXT",
        "shift_id": "INTEGER",
    },
    "production_orders": {
        "linked_entry_id": "INTEGER",
        "linked_entry_type": "TEXT",
        "raw_warehouse_id": "INTEGER",
        "output_warehouse_id": "INTEGER",
    },
    "audit_log": {
        "event_time": "TEXT",
        "entity_type": "TEXT",
        "entity_id": "INTEGER",
        "old_values": "TEXT",
        "new_values": "TEXT",
        "session_id": "TEXT",
        "source": "TEXT",
    },
}

CORE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    version INTEGER PRIMARY KEY,
    applied_at TEXT DEFAULT CURRENT_TIMESTAMP,
    description TEXT
);

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
    UNIQUE(user_id, name)
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
    updated_at TEXT
);

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
    shift_id INTEGER
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
    notes TEXT
);

CREATE TABLE IF NOT EXISTS item_warehouse_balances (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    item_id INTEGER NOT NULL,
    warehouse_id INTEGER NOT NULL,
    quantity TEXT DEFAULT '0',
    average_cost TEXT DEFAULT '0',
    updated_at TEXT,
    UNIQUE(user_id, item_id, warehouse_id)
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
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
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
    created_at TEXT
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
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_inventory_ledger_ref ON inventory_ledger(reference_type, reference_id);
CREATE INDEX IF NOT EXISTS idx_inventory_ledger_item_date ON inventory_ledger(item_id, movement_date);

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

"""


def _actual_table_name(cursor, table_name):
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND lower(name)=lower(?) LIMIT 1", (table_name,))
    row = cursor.fetchone()
    return row[0] if row else None


def _table_exists(cursor, table_name):
    return _actual_table_name(cursor, table_name) is not None


def _column_names(cursor, table_name):
    actual = _actual_table_name(cursor, table_name)
    if not actual:
        return set()
    cursor.execute(f"PRAGMA table_info({actual})")
    return {row[1] for row in cursor.fetchall()}


def _add_missing_columns(cursor, table_name, columns):
    existing = _column_names(cursor, table_name)
    if not existing:
        return
    for name, definition in columns.items():
        if name not in existing:
            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {name} {definition}")


def apply_common_schema(conn):
    """Apply idempotent schema upgrades shared by client and server."""
    cursor = conn.cursor()
    cursor.executescript(CORE_TABLES_SQL)
    for table_name, columns in REQUIRED_COLUMNS.items():
        _add_missing_columns(cursor, table_name, columns)

    conditional_indexes = {
        "inventory_movements": [
            "CREATE INDEX IF NOT EXISTS idx_inventory_movements_item ON inventory_movements(item_id)",
            "CREATE INDEX IF NOT EXISTS idx_inventory_movements_ref ON inventory_movements(reference_id, movement_type)",
        ],
        "invoices": [
            "CREATE INDEX IF NOT EXISTS idx_invoices_branch ON invoices(branch_id)",
            "CREATE INDEX IF NOT EXISTS idx_invoices_warehouse ON invoices(warehouse_id)",
            "CREATE INDEX IF NOT EXISTS idx_invoices_shift ON invoices(shift_id)",
        ],
        "vouchers": ["CREATE INDEX IF NOT EXISTS idx_vouchers_branch ON vouchers(branch_id)"],
        "expenses": ["CREATE INDEX IF NOT EXISTS idx_expenses_branch ON expenses(branch_id)"],
        "warehouses": ["CREATE INDEX IF NOT EXISTS idx_warehouses_branch ON warehouses(branch_id)"],
        "cash_bank_movements": [
            "CREATE INDEX IF NOT EXISTS idx_cash_mov_ref ON cash_bank_movements(reference_type, reference_id)",
            "CREATE INDEX IF NOT EXISTS idx_cash_mov_shift ON cash_bank_movements(shift_id)",
        ],
        "pos_shifts": ["CREATE INDEX IF NOT EXISTS idx_pos_shifts_user_status ON pos_shifts(user_id, status)"],
    }
    for table_name, statements in conditional_indexes.items():
        if _table_exists(cursor, table_name):
            for statement in statements:
                cursor.execute(statement)

    # Safe normalization for old data created before branch/warehouse modules.
    cursor.execute("UPDATE categories SET is_active=1 WHERE is_active IS NULL") if _table_exists(cursor, "categories") else None
    cursor.execute("UPDATE invoices SET payment_method='cash' WHERE payment_method IS NULL") if _table_exists(cursor, "invoices") else None
    cursor.execute("UPDATE vouchers SET payment_method='cash' WHERE payment_method IS NULL") if _table_exists(cursor, "vouchers") else None
    cursor.execute("UPDATE expenses SET payment_method='cash' WHERE payment_method IS NULL") if _table_exists(cursor, "expenses") else None

    cursor.execute(
        "INSERT OR IGNORE INTO schema_migrations (version, description) VALUES (?, ?)",
        (SCHEMA_VERSION, "common client/server schema guard"),
    )
    cursor.execute(f"PRAGMA user_version={SCHEMA_VERSION}")
    conn.commit()
