import importlib.util
import sqlite3
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load_gateway(monkeypatch, tmp_path):
    class TempDatabaseConnection:
        def __init__(self):
            self.path = tmp_path / "restaurant_checkout.sqlite3"
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
    spec = importlib.util.spec_from_file_location("phase26_local_restaurant_gateway", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module.LocalRestaurantGateway()


def test_checkout_session_creates_sales_invoice_and_releases_table(monkeypatch, tmp_path):
    gateway = _load_gateway(monkeypatch, tmp_path)
    table = gateway.list_tables()[0]
    session = gateway.open_table(table["id"], guests=2)
    gateway.add_order_line(session["id"], item_name="Burger", item_id=None, quantity="2", unit_price="7.50")
    gateway.send_to_kitchen(session["id"])

    checked_out = gateway.checkout_session(session["id"], payment_method="cash")

    assert checked_out["status"] == "closed"
    assert checked_out["invoice_id"]
    assert checked_out["invoice_reference"].startswith("RST-")
    assert checked_out["invoice_total"] == "15.00"
    conn = gateway._conn()
    invoice = conn.execute("SELECT * FROM invoices WHERE id=?", (checked_out["invoice_id"],)).fetchone()
    assert invoice["type"] == "sale"
    assert invoice["status"] == "active"
    assert invoice["workflow_status"] == "POSTED"
    line = conn.execute("SELECT * FROM invoice_lines WHERE invoice_id=?", (checked_out["invoice_id"],)).fetchone()
    assert line["description"] == "Burger"
    assert line["total"] == "15.00"
    table_after = next(row for row in gateway.list_tables() if row["id"] == table["id"])
    assert table_after["status"] == "free"


def test_checkout_is_blocked_until_new_lines_are_sent(monkeypatch, tmp_path):
    gateway = _load_gateway(monkeypatch, tmp_path)
    table = gateway.list_tables()[0]
    session = gateway.open_table(table["id"])
    gateway.add_order_line(session["id"], item_name="Tea", quantity="1", unit_price="2")
    try:
        gateway.checkout_session(session["id"])
    except ValueError as exc:
        assert "kitchen" in str(exc).lower() or "send" in str(exc).lower()
    else:
        raise AssertionError("Checkout must be blocked while new lines are unsent")


def test_phase26_boundaries_and_ui_wiring():
    interface = (ROOT / 'alrajhi_client' / 'gateways' / 'restaurant_gateway.py').read_text(encoding='utf-8')
    local = (ROOT / 'alrajhi_client' / 'gateways' / 'local' / 'restaurant_gateway.py').read_text(encoding='utf-8')
    remote = (ROOT / 'alrajhi_client' / 'gateways' / 'remote' / 'restaurant_gateway.py').read_text(encoding='utf-8')
    service = (ROOT / 'alrajhi_client' / 'core' / 'services' / 'restaurant_service.py').read_text(encoding='utf-8')
    pos = (ROOT / 'alrajhi_client' / 'views' / 'restaurant' / 'restaurant_pos_widget.py').read_text(encoding='utf-8')
    routes = (ROOT / 'alrajhi_server' / 'services' / 'http_routes' / 'restaurant.py').read_text(encoding='utf-8')
    repo = (ROOT / 'alrajhi_server' / 'repositories' / 'restaurant_repository.py').read_text(encoding='utf-8')
    assert 'def checkout_session(' in interface
    assert 'def checkout_session(' in local
    assert '/api/restaurant/sessions/{int(session_id)}/checkout' in remote
    assert 'def checkout_session(' in service
    assert 'self.service.checkout_session' in pos
    assert '@restaurant_bp.route("/restaurant/sessions/<int:session_id>/checkout", methods=["POST"])' in routes
    assert 'def checkout_session(self, session_id: int, user_id: str' in repo
