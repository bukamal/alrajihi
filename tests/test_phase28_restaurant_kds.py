import importlib.util
import sqlite3
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load_gateway(monkeypatch, tmp_path):
    class TempDatabaseConnection:
        def __init__(self):
            self.path = tmp_path / "restaurant_kds.sqlite3"
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
    spec = importlib.util.spec_from_file_location("phase28_local_restaurant_gateway", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module.LocalRestaurantGateway()


def test_kitchen_ticket_lifecycle_updates_ticket_and_lines(monkeypatch, tmp_path):
    gateway = _load_gateway(monkeypatch, tmp_path)
    table = gateway.list_tables()[0]
    session = gateway.open_table(table["id"])
    gateway.add_order_line(session["id"], item_name="Burger", quantity="1", unit_price="9")
    gateway.add_order_line(session["id"], item_name="Soup", quantity="2", unit_price="4")
    sent = gateway.send_to_kitchen(session["id"])
    ticket_id = sent["ticket"]["id"]

    tickets = gateway.list_kitchen_tickets(status="all")
    assert any(ticket["id"] == ticket_id for ticket in tickets)
    detail = gateway.get_kitchen_ticket(ticket_id)
    assert len(detail["lines"]) == 2

    ready = gateway.update_kitchen_ticket_status(ticket_id, "ready")
    assert ready["status"] == "ready"
    refreshed = gateway.get_session(session["id"])
    assert {line["kitchen_status"] for line in refreshed["lines"]} == {"ready"}


def test_phase28_kds_boundaries_ui_and_translations():
    interface = (ROOT / 'alrajhi_client' / 'gateways' / 'restaurant_gateway.py').read_text(encoding='utf-8')
    local = (ROOT / 'alrajhi_client' / 'gateways' / 'local' / 'restaurant_gateway.py').read_text(encoding='utf-8')
    remote = (ROOT / 'alrajhi_client' / 'gateways' / 'remote' / 'restaurant_gateway.py').read_text(encoding='utf-8')
    service = (ROOT / 'alrajhi_client' / 'core' / 'services' / 'restaurant_service.py').read_text(encoding='utf-8')
    routes = (ROOT / 'alrajhi_server' / 'services' / 'http_routes' / 'restaurant.py').read_text(encoding='utf-8')
    dashboard = (ROOT / 'alrajhi_client' / 'views' / 'restaurant' / 'restaurant_dashboard.py').read_text(encoding='utf-8')
    kds = (ROOT / 'alrajhi_client' / 'views' / 'restaurant' / 'kitchen_display_widget.py').read_text(encoding='utf-8')
    translator = (ROOT / 'alrajhi_client' / 'i18n' / 'translator.py').read_text(encoding='utf-8')
    qss = (ROOT / 'alrajhi_client' / 'theme' / 'qss.py').read_text(encoding='utf-8')

    assert 'list_kitchen_tickets' in interface
    assert 'get_kitchen_ticket' in local
    assert '/api/restaurant/kitchen/tickets' in remote
    assert 'update_kitchen_ticket_status' in service
    assert '@restaurant_bp.route("/restaurant/kitchen/tickets", methods=["GET"])' in routes
    assert 'KitchenDisplayWidget' in dashboard
    assert 'restaurantKitchenDisplay' in kds
    assert "'restaurant.kds.title': 'شاشة المطبخ'" in translator
    assert "'restaurant.kds.title': 'Küchenanzeige'" in translator
    assert "'restaurant.kds.title': 'Kitchen display'" in translator
    assert 'Phase 28: restaurant kitchen display system' in qss
