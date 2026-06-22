import sqlite3

from alrajhi_client.database.schema_manager import apply_common_schema as apply_client_schema
from alrajhi_server.database.schema_manager import apply_common_schema as apply_server_schema


def _legacy_database_with_old_warehouse_movements():
    conn = sqlite3.connect(":memory:")
    conn.executescript(
        """
        CREATE TABLE schema_migrations (version INTEGER PRIMARY KEY, description TEXT);
        CREATE TABLE users (id TEXT PRIMARY KEY);
        CREATE TABLE items (id INTEGER PRIMARY KEY, user_id TEXT, name TEXT);
        CREATE TABLE warehouses (id INTEGER PRIMARY KEY, user_id TEXT, name TEXT);
        CREATE TABLE item_variants (
            id INTEGER PRIMARY KEY,
            user_id TEXT,
            item_id INTEGER,
            color TEXT,
            size TEXT,
            sku TEXT,
            barcode TEXT
        );
        CREATE TABLE item_warehouse_variant_balances (
            id INTEGER PRIMARY KEY,
            user_id TEXT,
            item_id INTEGER,
            variant_id INTEGER,
            warehouse_id INTEGER
        );
        CREATE TABLE warehouse_movements (
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
        CREATE TABLE warehouse_transfers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            transfer_no TEXT NOT NULL,
            item_id INTEGER NOT NULL,
            from_warehouse_id INTEGER NOT NULL,
            to_warehouse_id INTEGER NOT NULL,
            quantity TEXT NOT NULL
        );
        """
    )
    return conn


def _column_names(conn, table):
    return {row[1] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}


def _index_names(conn, table):
    return {row[1] for row in conn.execute(f"PRAGMA index_list({table})").fetchall()}


def _assert_variant_upgrade(apply_schema):
    conn = _legacy_database_with_old_warehouse_movements()
    apply_schema(conn)

    warehouse_columns = _column_names(conn, "warehouse_movements")
    for column in (
        "variant_id",
        "variant_color",
        "variant_size",
        "variant_sku",
        "barcode_scope",
        "matched_barcode",
    ):
        assert column in warehouse_columns

    transfer_columns = _column_names(conn, "warehouse_transfers")
    for column in ("variant_id", "variant_color", "variant_size", "variant_sku"):
        assert column in transfer_columns

    balance_columns = _column_names(conn, "item_warehouse_variant_balances")
    for column in ("variant_color", "variant_size", "variant_sku", "quantity", "average_cost", "updated_at"):
        assert column in balance_columns

    assert "idx_wh_mov_variant" in _index_names(conn, "warehouse_movements")


def test_phase323_client_startup_adds_variant_columns_before_indexes():
    _assert_variant_upgrade(apply_client_schema)


def test_phase323_server_startup_adds_variant_columns_before_indexes():
    _assert_variant_upgrade(apply_server_schema)
