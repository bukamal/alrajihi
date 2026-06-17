import importlib.util
import sqlite3
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load_gateway(monkeypatch, tmp_path):
    class TempDatabaseConnection:
        def __init__(self):
            self.path = tmp_path / "restaurant_phase31.sqlite3"
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
    spec = importlib.util.spec_from_file_location("phase31_local_restaurant_gateway", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module.LocalRestaurantGateway()


def test_kitchen_stations_split_kot_by_assigned_station(monkeypatch, tmp_path):
    gateway = _load_gateway(monkeypatch, tmp_path)
    stations = gateway.list_kitchen_stations()
    assert {station["code"] for station in stations} >= {"bar", "grill", "hot", "dessert"}
    bar = next(st for st in stations if st["code"] == "bar")
    grill = next(st for st in stations if st["code"] == "grill")

    gateway.assign_menu_item_station(item_id=101, station_id=bar["id"])
    gateway.assign_menu_item_station(item_id=202, station_id=grill["id"])

    table = gateway.list_tables()[0]
    session = gateway.open_table(table["id"], guests=2)
    gateway.add_order_line(session["id"], item_id=101, item_name="Cola", quantity="2", unit_price="3")
    gateway.add_order_line(session["id"], item_id=202, item_name="Steak", quantity="1", unit_price="18")

    sent = gateway.send_to_kitchen(session["id"])
    assert len(sent["tickets"]) == 2
    station_names = {ticket["station"]["code"] for ticket in sent["tickets"]}
    assert station_names == {"bar", "grill"}

    bar_tickets = gateway.list_kitchen_tickets(status="all", station_id=bar["id"])
    assert len(bar_tickets) == 1
    assert bar_tickets[0]["station_code"] == "bar"
    detail = gateway.get_kitchen_ticket(bar_tickets[0]["id"])
    assert detail["station_code"] == "bar"
    assert detail["lines"][0]["item_name"] == "Cola"


def test_phase31_contracts_routes_kds_and_translations():
    interface = (ROOT / 'alrajhi_client' / 'gateways' / 'restaurant_gateway.py').read_text(encoding='utf-8')
    local = (ROOT / 'alrajhi_client' / 'gateways' / 'local' / 'restaurant_gateway.py').read_text(encoding='utf-8')
    remote = (ROOT / 'alrajhi_client' / 'gateways' / 'remote' / 'restaurant_gateway.py').read_text(encoding='utf-8')
    service = (ROOT / 'alrajhi_client' / 'core' / 'services' / 'restaurant_service.py').read_text(encoding='utf-8')
    routes = (ROOT / 'alrajhi_server' / 'services' / 'http_routes' / 'restaurant.py').read_text(encoding='utf-8')
    repo = (ROOT / 'alrajhi_server' / 'repositories' / 'restaurant_repository.py').read_text(encoding='utf-8')
    kds = (ROOT / 'alrajhi_client' / 'views' / 'restaurant' / 'kitchen_display_widget.py').read_text(encoding='utf-8')
    translator = (ROOT / 'alrajhi_client' / 'i18n' / 'translator.py').read_text(encoding='utf-8')

    for name in ('list_kitchen_stations', 'upsert_kitchen_station', 'assign_menu_item_station'):
        assert name in interface
        assert name in local
        assert name in remote
        assert name in service
        assert name in repo
    assert '/restaurant/kitchen/stations' in routes
    assert '/restaurant/menu_items/<int:item_id>/station' in routes
    assert 'station_id' in repo
    assert 'restaurantKDSStationFilter' in kds
    assert 'restaurant.kds.all_stations' in translator
