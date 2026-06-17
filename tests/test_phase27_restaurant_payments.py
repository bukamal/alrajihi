import importlib.util
import sqlite3
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load_gateway(monkeypatch, tmp_path):
    class TempDatabaseConnection:
        def __init__(self):
            self.path = tmp_path / "restaurant_payments.sqlite3"
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
    spec = importlib.util.spec_from_file_location("phase27_local_restaurant_gateway", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module.LocalRestaurantGateway()


def test_restaurant_split_payments_must_cover_full_balance_before_checkout(monkeypatch, tmp_path):
    gateway = _load_gateway(monkeypatch, tmp_path)
    table = gateway.list_tables()[0]
    session = gateway.open_table(table["id"], guests=3)
    gateway.add_order_line(session["id"], item_name="Pizza", quantity="2", unit_price="8.00")
    gateway.add_order_line(session["id"], item_name="Water", quantity="1", unit_price="2.00")
    gateway.send_to_kitchen(session["id"])

    first = gateway.record_payment(session["id"], amount="10", payment_method="cash")
    assert first["paid"] == "10"
    assert first["remaining"] == "8.00"
    try:
        gateway.checkout_session(session["id"], paid_amount="0", payment_method="cash")
    except ValueError as exc:
        assert "fully paid" in str(exc).lower()
    else:
        raise AssertionError("Restaurant checkout must not close a partially paid table")

    second = gateway.record_payment(session["id"], amount="99", payment_method="card")
    assert second["paid"] == "18.00"
    assert second["remaining"] == "0.00"
    checked_out = gateway.checkout_session(session["id"], paid_amount="0", payment_method="card")
    assert checked_out["invoice_id"]
    assert checked_out["paid_amount"] == "18.00"
    payments = gateway._conn().execute("SELECT * FROM restaurant_payments WHERE session_id=? ORDER BY id", (session["id"],)).fetchall()
    assert len(payments) == 2
    assert all(row["invoice_id"] == checked_out["invoice_id"] for row in payments)


def test_phase27_payment_boundaries_and_ui_wiring():
    interface = (ROOT / 'alrajhi_client' / 'gateways' / 'restaurant_gateway.py').read_text(encoding='utf-8')
    local = (ROOT / 'alrajhi_client' / 'gateways' / 'local' / 'restaurant_gateway.py').read_text(encoding='utf-8')
    remote = (ROOT / 'alrajhi_client' / 'gateways' / 'remote' / 'restaurant_gateway.py').read_text(encoding='utf-8')
    service = (ROOT / 'alrajhi_client' / 'core' / 'services' / 'restaurant_service.py').read_text(encoding='utf-8')
    pos = (ROOT / 'alrajhi_client' / 'views' / 'restaurant' / 'restaurant_pos_widget.py').read_text(encoding='utf-8')
    routes = (ROOT / 'alrajhi_server' / 'services' / 'http_routes' / 'restaurant.py').read_text(encoding='utf-8')
    repo = (ROOT / 'alrajhi_server' / 'repositories' / 'restaurant_repository.py').read_text(encoding='utf-8')
    translator = (ROOT / 'alrajhi_client' / 'i18n' / 'translator.py').read_text(encoding='utf-8')

    assert 'def record_payment(' in interface
    assert 'def session_balance(' in interface
    assert 'restaurant_payments' in local
    assert '/api/restaurant/sessions/{int(session_id)}/payments' in remote
    assert 'def record_payment(' in service
    assert 'RestaurantPaymentDialog' in pos
    assert '@restaurant_bp.route("/restaurant/sessions/<int:session_id>/payments", methods=["POST"])' in routes
    assert 'def record_payment(self, session_id: int' in repo
    assert "'restaurant.record_payment': 'تسجيل دفعة'" in translator
    assert "'restaurant.record_payment': 'Zahlung buchen'" in translator
    assert "'restaurant.record_payment': 'Record payment'" in translator
