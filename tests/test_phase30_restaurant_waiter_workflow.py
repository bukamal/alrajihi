import importlib.util
import sqlite3
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load_gateway(monkeypatch, tmp_path):
    class TempDatabaseConnection:
        def __init__(self):
            self.path = tmp_path / "restaurant_phase30.sqlite3"
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
    spec = importlib.util.spec_from_file_location("phase30_local_restaurant_gateway", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module.LocalRestaurantGateway()


def test_waiter_workflow_assign_call_resolve_and_metrics(monkeypatch, tmp_path):
    gateway = _load_gateway(monkeypatch, tmp_path)
    table = gateway.list_tables()[0]
    session = gateway.open_table(table["id"], guests=2)

    assigned = gateway.assign_waiter(session["id"], waiter_id="waiter-7", notes="front section")
    assert assigned["waiter_id"] == "waiter-7"
    assert assigned["service_started_at"]

    line = gateway.add_order_line(session["id"], item_name="Tea", quantity="1", unit_price="2")
    gateway.update_line_status(line["id"], "cancelled")

    called = gateway.call_waiter(session["id"], notes="guest needs water")
    assert called["waiter_call_pending"] is True
    assert called["waiter_call_status"] == "open"

    resolved = gateway.resolve_waiter_call(session["id"], notes="handled")
    assert resolved["waiter_call_status"] == "resolved"

    summary = gateway.waiter_session_summary(session["id"])
    assert summary["waiter_id"] == "waiter-7"
    assert summary["modification_count"] >= 2
    assert summary["cancelled_line_count"] == 1
    assert summary["event_counts"]["waiter_assigned"] == 1
    assert summary["event_counts"]["waiter_called"] == 1
    assert summary["event_counts"]["waiter_call_resolved"] == 1


def test_phase30_contracts_routes_translations_and_boundaries():
    interface = (ROOT / 'alrajhi_client' / 'gateways' / 'restaurant_gateway.py').read_text(encoding='utf-8')
    local = (ROOT / 'alrajhi_client' / 'gateways' / 'local' / 'restaurant_gateway.py').read_text(encoding='utf-8')
    remote = (ROOT / 'alrajhi_client' / 'gateways' / 'remote' / 'restaurant_gateway.py').read_text(encoding='utf-8')
    service = (ROOT / 'alrajhi_client' / 'core' / 'services' / 'restaurant_service.py').read_text(encoding='utf-8')
    routes = (ROOT / 'alrajhi_server' / 'services' / 'http_routes' / 'restaurant.py').read_text(encoding='utf-8')
    repo = (ROOT / 'alrajhi_server' / 'repositories' / 'restaurant_repository.py').read_text(encoding='utf-8')
    translator = (ROOT / 'alrajhi_client' / 'i18n' / 'translator.py').read_text(encoding='utf-8')

    for name in ('assign_waiter', 'call_waiter', 'resolve_waiter_call', 'waiter_session_summary'):
        assert name in interface
        assert name in local
        assert name in remote
        assert name in service
        assert name in repo
    assert '/restaurant/sessions/<int:session_id>/waiter' in routes
    assert '/restaurant/sessions/<int:session_id>/waiter_call' in routes
    assert 'restaurant_service_events' in repo
    assert 'restaurant.waiter.assign' in translator
