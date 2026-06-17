import importlib.util
import sqlite3
import sys
import types
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load_gateway(monkeypatch, tmp_path):
    class TempDatabaseConnection:
        def __init__(self):
            self.path = tmp_path / "restaurant_phase34.sqlite3"
            self.conn = sqlite3.connect(self.path)
            self.conn.row_factory = sqlite3.Row
            self.conn.execute("PRAGMA foreign_keys=ON")
            self.conn.executescript(
                """
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
                    workflow_status TEXT DEFAULT 'DRAFT',
                    original_currency TEXT DEFAULT 'USD',
                    payment_method TEXT DEFAULT 'cash'
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
                    conversion_factor REAL DEFAULT 1.0,
                    FOREIGN KEY(invoice_id) REFERENCES invoices(id) ON DELETE CASCADE
                );
                CREATE TABLE IF NOT EXISTS items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    category_id INTEGER,
                    selling_price TEXT,
                    unit TEXT,
                    barcode TEXT,
                    quantity TEXT,
                    deleted_at TEXT
                );
                """
            )
            self.conn.commit()

        def get_connection(self):
            return self.conn

    database_pkg = types.ModuleType("database")
    connection_mod = types.ModuleType("database.connection")
    connection_mod.DatabaseConnection = TempDatabaseConnection
    gateways_pkg = types.ModuleType("gateways")
    restaurant_gateway_mod = types.ModuleType("gateways.restaurant_gateway")
    restaurant_gateway_mod.RestaurantGateway = object

    monkeypatch.setitem(sys.modules, "database", database_pkg)
    monkeypatch.setitem(sys.modules, "database.connection", connection_mod)
    monkeypatch.setitem(sys.modules, "gateways", gateways_pkg)
    monkeypatch.setitem(sys.modules, "gateways.restaurant_gateway", restaurant_gateway_mod)

    path = ROOT / "alrajhi_client" / "gateways" / "local" / "restaurant_gateway.py"
    spec = importlib.util.spec_from_file_location("phase34_local_restaurant_gateway", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module.LocalRestaurantGateway()


def test_phase34_modifiers_affect_line_and_session_total(monkeypatch, tmp_path):
    gateway = _load_gateway(monkeypatch, tmp_path)
    session = gateway.open_table(gateway.list_tables()[0]["id"], guests=2)
    line = gateway.add_order_line(session["id"], item_name="Pizza", quantity="1", unit_price="10")
    group = gateway.upsert_modifier_group(item_id=None, name="Pizza options", max_selected=5)
    extra = gateway.upsert_modifier_option(group["id"], name="Extra cheese", price_delta="2", kitchen_label="+ cheese")
    gateway.add_order_line_modifier(line["id"], option_id=extra["id"])

    refreshed = gateway.get_order_line(line["id"])
    balance = gateway.session_balance(session["id"])

    assert Decimal(refreshed["modifier_total"]) == Decimal("2")
    assert Decimal(refreshed["line_total"]) == Decimal("12")
    assert Decimal(balance["subtotal"]) == Decimal("12")


def test_phase34_recipe_consumption_is_idempotent_and_updates_inventory(monkeypatch, tmp_path):
    gateway = _load_gateway(monkeypatch, tmp_path)
    conn = gateway._conn()
    conn.execute("INSERT INTO items(id, name, selling_price, quantity) VALUES (1, 'Burger', '8', '0')")
    conn.execute("INSERT INTO items(id, name, selling_price, quantity) VALUES (2, 'Bun', '0', '10')")
    conn.commit()
    session = gateway.open_table(gateway.list_tables()[0]["id"], guests=1)
    gateway.upsert_recipe(1, name="Burger recipe", yield_quantity="1", lines=[{"component_item_id": 2, "component_name": "Bun", "quantity": "1", "unit": "pc"}])
    gateway.add_order_line(session["id"], item_id=1, item_name="Burger", quantity="2", unit_price="8")
    gateway.send_to_kitchen(session["id"])

    first = gateway.consume_session_recipes(session["id"], invoice_id=99)
    second = gateway.consume_session_recipes(session["id"], invoice_id=99)
    qty = conn.execute("SELECT quantity FROM items WHERE id=2").fetchone()["quantity"]

    assert first["count"] == 1
    assert second["count"] == 0
    assert Decimal(str(qty)) == Decimal("8")
