import importlib.util
import sqlite3
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load_gateway(monkeypatch, tmp_path):
    class TempDatabaseConnection:
        def __init__(self):
            self.path = tmp_path / "restaurant_phase29.sqlite3"
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
    spec = importlib.util.spec_from_file_location("phase29_local_restaurant_gateway", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module.LocalRestaurantGateway()


def test_table_transfer_split_merge_and_reservation(monkeypatch, tmp_path):
    gateway = _load_gateway(monkeypatch, tmp_path)
    tables = gateway.list_tables()
    assert len(tables) >= 4

    reservation = gateway.reserve_table(tables[2]["id"], customer_name="Guest", phone="123", guests=2)
    assert reservation["status"] == "reserved"
    assert {t["id"]: t for t in gateway.list_tables()}[tables[2]["id"]]["status"] == "reserved"
    cancelled = gateway.cancel_reservation(reservation["id"])
    assert cancelled["status"] == "cancelled"

    source = gateway.open_table(tables[0]["id"], guests=2)
    line_a = gateway.add_order_line(source["id"], item_name="Soup", quantity="1", unit_price="4")
    line_b = gateway.add_order_line(source["id"], item_name="Steak", quantity="1", unit_price="15")

    moved = gateway.transfer_session(source["id"], tables[1]["id"])
    assert moved["table_id"] == tables[1]["id"]

    split = gateway.split_lines_to_table(moved["id"], [line_b["id"]], tables[3]["id"])
    assert split["target_session"]["table_id"] == tables[3]["id"]
    assert [line["id"] for line in split["target_session"]["lines"]] == [line_b["id"]]

    merged = gateway.merge_sessions(split["target_session"]["id"], moved["id"])
    merged_line_ids = {line["id"] for line in merged["lines"]}
    assert {line_a["id"], line_b["id"]}.issubset(merged_line_ids)


def test_phase29_boundaries_routes_and_gateway_contracts():
    interface = (ROOT / 'alrajhi_client' / 'gateways' / 'restaurant_gateway.py').read_text(encoding='utf-8')
    local = (ROOT / 'alrajhi_client' / 'gateways' / 'local' / 'restaurant_gateway.py').read_text(encoding='utf-8')
    remote = (ROOT / 'alrajhi_client' / 'gateways' / 'remote' / 'restaurant_gateway.py').read_text(encoding='utf-8')
    service = (ROOT / 'alrajhi_client' / 'core' / 'services' / 'restaurant_service.py').read_text(encoding='utf-8')
    routes = (ROOT / 'alrajhi_server' / 'services' / 'http_routes' / 'restaurant.py').read_text(encoding='utf-8')
    repo = (ROOT / 'alrajhi_server' / 'repositories' / 'restaurant_repository.py').read_text(encoding='utf-8')

    for name in ('reserve_table', 'transfer_session', 'merge_sessions', 'split_lines_to_table'):
        assert name in interface
        assert name in local
        assert name in remote
        assert name in service
        assert name in repo
    assert '/restaurant/sessions/<int:session_id>/transfer' in routes
    assert '/restaurant/sessions/<int:target_session_id>/merge' in routes
    assert '/restaurant/sessions/<int:session_id>/split_lines' in routes
