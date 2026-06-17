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
            self.path = tmp_path / "restaurant_adjustments.sqlite3"
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
    spec = importlib.util.spec_from_file_location("phase33_local_restaurant_gateway", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module.LocalRestaurantGateway()


def test_restaurant_adjustments_affect_balance(monkeypatch, tmp_path):
    gateway = _load_gateway(monkeypatch, tmp_path)
    session = gateway.open_table(gateway.list_tables()[0]["id"], guests=2)
    gateway.add_order_line(session["id"], item_name="Meal", quantity="2", unit_price="10")
    gateway.send_to_kitchen(session["id"])
    balance = gateway.set_session_adjustments(session["id"], discount_amount="3", service_charge_amount="2", tax_amount="1")

    assert Decimal(balance["subtotal"]) == Decimal("20")
    assert Decimal(balance["discount_amount"]) == Decimal("3")
    assert Decimal(balance["service_charge_amount"]) == Decimal("2")
    assert Decimal(balance["tax_amount"]) == Decimal("1")
    assert Decimal(balance["total"]) == Decimal("20")


def test_restaurant_adjustments_post_to_invoice(monkeypatch, tmp_path):
    gateway = _load_gateway(monkeypatch, tmp_path)
    session = gateway.open_table(gateway.list_tables()[0]["id"], guests=1)
    gateway.add_order_line(session["id"], item_name="Meal", quantity="1", unit_price="10")
    gateway.send_to_kitchen(session["id"])
    gateway.set_session_adjustments(session["id"], discount_amount="1", service_charge_amount="2", tax_amount="3")
    gateway.record_payment(session["id"], amount="14", payment_method="cash")
    checkout = gateway.checkout_session(session["id"], paid_amount="0", payment_method="cash")
    lines = gateway._conn().execute("SELECT description, total FROM invoice_lines WHERE invoice_id=? ORDER BY id", (checkout["invoice_id"],)).fetchall()
    descriptions = [row["description"] for row in lines]
    assert "Restaurant discount" in descriptions
    assert "Restaurant service charge" in descriptions
    assert "Restaurant tax" in descriptions
