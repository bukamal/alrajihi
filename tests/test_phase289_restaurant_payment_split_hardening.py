import importlib.util
import sqlite3
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load_gateway(monkeypatch, tmp_path):
    class TempDatabaseConnection:
        def __init__(self):
            self.path = tmp_path / "restaurant_payment_split_phase289.sqlite3"
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
    spec = importlib.util.spec_from_file_location("phase289_local_restaurant_gateway", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module.LocalRestaurantGateway()


def _opened_billable_session(gateway):
    table = gateway.list_tables()[0]
    session = gateway.open_table(table["id"])
    line1 = gateway.add_order_line(session["id"], item_name="Soup", quantity="2", unit_price="5")
    line2 = gateway.add_order_line(session["id"], item_name="Steak", quantity="1", unit_price="20")
    gateway.send_to_kitchen(session["id"])
    return session, line1, line2


def test_split_bill_caps_overpayment_and_blocks_duplicate_lines(monkeypatch, tmp_path):
    gateway = _load_gateway(monkeypatch, tmp_path)
    session, line1, _line2 = _opened_billable_session(gateway)

    result = gateway.create_split_bills(session["id"], [{
        "guest_label": "Guest 1",
        "line_ids": [line1["id"]],
        "paid_amount": "999",
        "payment_method": "card",
    }])
    split = result["split_bills"][0]
    assert split["subtotal"] == "10"
    assert split["paid_amount"] == "10"
    assert split["remaining_amount"] == "0"
    assert split["status"] == "paid"
    assert result["balance"]["paid"] == "10"

    try:
        gateway.create_split_bills(session["id"], [{"line_ids": [line1["id"]]}])
    except ValueError as exc:
        assert "already" in str(exc).lower()
    else:
        raise AssertionError("Existing split lines must not be assigned twice")


def test_partial_and_mixed_payments_block_checkout_until_fully_paid(monkeypatch, tmp_path):
    gateway = _load_gateway(monkeypatch, tmp_path)
    session, _line1, line2 = _opened_billable_session(gateway)

    balance = gateway.record_payment(session["id"], amount="5", payment_method="cash")
    assert balance["remaining"] == "25"
    try:
        gateway.checkout_session(session["id"], paid_amount="0", payment_method="cash")
    except ValueError as exc:
        assert "fully paid" in str(exc).lower()
    else:
        raise AssertionError("Checkout must remain blocked until the bill is fully paid")

    split = gateway.create_split_bills(session["id"], [{"line_ids": [line2["id"]], "paid_amount": "0"}])["split_bills"][0]
    paid = gateway.pay_split_bill(split["id"], amount="999", payment_method="bank")
    assert paid["applied_amount"] == "20"
    assert paid["remaining_amount"] == "0"

    final_balance = gateway.record_payment(session["id"], amount="5", payment_method="card")
    assert final_balance["is_fully_paid"] is True
    closed = gateway.checkout_session(session["id"], paid_amount="0", payment_method="mixed")
    assert closed["status"] == "closed"


def test_phase289_contract_files_are_wired():
    policy = (ROOT / "alrajhi_client" / "features" / "restaurant" / "restaurant_payment_split_policy.py").read_text(encoding="utf-8")
    local = (ROOT / "alrajhi_client" / "gateways" / "local" / "restaurant_gateway.py").read_text(encoding="utf-8")
    ui = (ROOT / "alrajhi_client" / "views" / "restaurant" / "restaurant_pos_widget.py").read_text(encoding="utf-8")
    release_gate = (ROOT / "alrajhi_client" / "workspace" / "quality" / "release_gate_contract.py").read_text(encoding="utf-8")
    assert "cap_payment" in policy
    assert "Order line already belongs to an existing split bill" in local
    assert "split_selected_line_payment" in ui
    assert "restaurant_payment_split" in release_gate
