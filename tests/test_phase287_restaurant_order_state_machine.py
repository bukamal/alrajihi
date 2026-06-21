from decimal import Decimal
import importlib.util
import sqlite3
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load_gateway(monkeypatch, tmp_path):
    class TempDatabaseConnection:
        def __init__(self):
            self.path = tmp_path / "restaurant_state_machine.sqlite3"
            self.conn = sqlite3.connect(self.path)
            self.conn.row_factory = sqlite3.Row
            self.conn.execute("PRAGMA foreign_keys=ON")
            self.conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS invoices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    type TEXT,
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
                    conversion_factor REAL DEFAULT 1.0
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

    connection_mod = types.ModuleType("database.connection")
    connection_mod.DatabaseConnection = TempDatabaseConnection
    restaurant_gateway_mod = types.ModuleType("gateways.restaurant_gateway")
    restaurant_gateway_mod.RestaurantGateway = object
    monkeypatch.setitem(sys.modules, "database.connection", connection_mod)
    monkeypatch.setitem(sys.modules, "gateways.restaurant_gateway", restaurant_gateway_mod)

    path = ROOT / "alrajhi_client" / "gateways" / "local" / "restaurant_gateway.py"
    spec = importlib.util.spec_from_file_location("phase287_local_restaurant_gateway", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module.LocalRestaurantGateway()


def _table_payload(gateway, table_id):
    return next(table for table in gateway.list_tables() if int(table["id"]) == int(table_id))


def test_order_state_machine_drives_table_payload(monkeypatch, tmp_path):
    gateway = _load_gateway(monkeypatch, tmp_path)
    table = gateway.list_tables()[0]
    session = gateway.open_table(table["id"])
    line = gateway.add_order_line(session["id"], item_name="Soup", quantity="2", unit_price="5")

    session = gateway.get_session(session["id"])
    assert session["order_state"] == "editing"
    table_payload = _table_payload(gateway, table["id"])
    assert table_payload["active_order_state"] == "editing"
    assert table_payload["ui_status"] if "ui_status" in table_payload else "occupied"

    sent = gateway.send_to_kitchen(session["id"])
    assert sent["ticket"]
    table_payload = _table_payload(gateway, table["id"])
    assert table_payload["active_order_state"] == "kitchen"
    assert table_payload["ui_status"] == "kitchen"

    gateway.update_kitchen_ticket_status(sent["ticket"]["id"], "ready")
    table_payload = _table_payload(gateway, table["id"])
    assert table_payload["active_order_state"] == "ready"
    assert table_payload["ui_status"] == "ready"

    gateway.update_kitchen_ticket_status(sent["ticket"]["id"], "served")
    table_payload = _table_payload(gateway, table["id"])
    assert table_payload["active_order_state"] == "payment_due"
    assert table_payload["ui_status"] == "payment"

    balance = gateway.record_payment(session["id"], amount="10", payment_method="cash")
    assert balance["is_fully_paid"] is True
    table_payload = _table_payload(gateway, table["id"])
    assert table_payload["active_order_state"] == "paid"
    assert table_payload["ui_status"] == "payment"

    closed = gateway.checkout_session(session["id"], paid_amount="0", payment_method="cash")
    assert closed["status"] == "closed"
    assert _table_payload(gateway, table["id"])["status"] == "free"


def test_order_state_helpers_are_explicit():
    from alrajhi_client.features.restaurant.restaurant_order_state import derive_order_state, derive_table_state

    lines = [{"kitchen_status": "new"}]
    assert derive_order_state(lines, {"total": "1", "paid": "0", "remaining": "1"}) == "editing"
    lines = [{"kitchen_status": "preparing"}]
    assert derive_table_state(lines, {"total": "1", "paid": "0", "remaining": "1"}) == "kitchen"
    lines = [{"kitchen_status": "served"}]
    assert derive_table_state(lines, {"total": "1", "paid": "0", "remaining": "1"}) == "payment"
    assert derive_table_state(lines, {"total": "1", "paid": "1", "remaining": "0"}) == "payment"


def test_phase287_ui_contract_is_present():
    pos = (ROOT / "alrajhi_client" / "views" / "restaurant" / "restaurant_pos_widget.py").read_text(encoding="utf-8")
    table_map = (ROOT / "alrajhi_client" / "views" / "restaurant" / "table_map_widget.py").read_text(encoding="utf-8")
    qss = (ROOT / "alrajhi_client" / "theme" / "qss.py").read_text(encoding="utf-8")
    translations = (ROOT / "alrajhi_client" / "i18n" / "translator.py").read_text(encoding="utf-8")
    assert "restaurantPOSStateBadge" in pos
    assert "_session_order_state" in pos
    assert "active_order_state" in table_map
    assert "restaurantPOSStateBadge" in qss
    assert "restaurant.order_state.payment_due" in translations
