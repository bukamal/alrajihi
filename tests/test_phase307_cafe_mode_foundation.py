# -*- coding: utf-8 -*-
import importlib.util
import sqlite3
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load_gateway(monkeypatch, tmp_path):
    class TempDatabaseConnection:
        def __init__(self):
            self.path = tmp_path / "cafe_mode.sqlite3"
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
                    average_cost TEXT,
                    purchase_price TEXT,
                    deleted_at TEXT
                );
                CREATE TABLE IF NOT EXISTS inventory_movements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    item_id INTEGER,
                    movement_type TEXT,
                    quantity TEXT,
                    unit_cost TEXT,
                    total_cost TEXT,
                    reference_id TEXT,
                    source_type TEXT,
                    source_key TEXT,
                    notes TEXT,
                    created_at TEXT
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
    spec = importlib.util.spec_from_file_location("phase307_local_restaurant_gateway", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module.LocalRestaurantGateway()


def test_local_cafe_quick_order_uses_hidden_virtual_table(monkeypatch, tmp_path):
    gateway = _load_gateway(monkeypatch, tmp_path)
    session = gateway.create_cafe_quick_order(customer_name="Walk-in", phone="", notes="espresso")

    assert session["status"] == "open"
    assert session["order_type"] == "cafe_quick_order"
    assert session["table_name"] == "Cafe"
    assert session["guests"] == 1

    visible_tables = gateway.list_tables()
    assert all(row.get("name") != "Cafe" for row in visible_tables)
    hidden = gateway._conn().execute("SELECT is_active FROM restaurant_tables WHERE name='Cafe'").fetchone()
    assert int(hidden["is_active"]) == 0

    gateway.add_order_line(session["id"], item_name="Espresso", quantity="2", unit_price="1.50")
    balance = gateway.session_balance(session["id"])
    assert balance["total"] == "3.00"


def test_phase307_cafe_mode_contracts_are_reused_not_separate():
    abstract_gateway = (ROOT / "alrajhi_client" / "gateways" / "restaurant_gateway.py").read_text(encoding="utf-8")
    local_gateway = (ROOT / "alrajhi_client" / "gateways" / "local" / "restaurant_gateway.py").read_text(encoding="utf-8")
    remote_gateway = (ROOT / "alrajhi_client" / "gateways" / "remote" / "restaurant_gateway.py").read_text(encoding="utf-8")
    service = (ROOT / "alrajhi_client" / "core" / "services" / "restaurant_service.py").read_text(encoding="utf-8")
    dashboard = (ROOT / "alrajhi_client" / "views" / "restaurant" / "restaurant_dashboard.py").read_text(encoding="utf-8")
    pos_widget = (ROOT / "alrajhi_client" / "views" / "restaurant" / "restaurant_pos_widget.py").read_text(encoding="utf-8")
    settings = (ROOT / "alrajhi_client" / "features" / "restaurant" / "restaurant_settings_contract.py").read_text(encoding="utf-8")
    routes = (ROOT / "alrajhi_server" / "services" / "http_routes" / "restaurant.py").read_text(encoding="utf-8")
    gate = (ROOT / "alrajhi_client" / "workspace" / "quality" / "release_gate_contract.py").read_text(encoding="utf-8")
    qss = (ROOT / "alrajhi_client" / "theme" / "qss.py").read_text(encoding="utf-8")

    assert "def create_cafe_quick_order" in abstract_gateway
    assert "order_type, customer_name, phone, delivery_status" in local_gateway
    assert "cafe_quick_order" in local_gateway
    assert "/restaurant/cafe_orders" in remote_gateway
    assert "restaurant_service.create_cafe_quick_order" in service
    assert "restaurantCafeModeButton" in dashboard
    assert "show_cafe_mode" in dashboard
    assert "RestaurantPOSWidget" in dashboard
    assert "restaurant.cafe_active_order" in pos_widget
    assert "quick_order_type" in settings
    assert '@restaurant_bp.route("/restaurant/cafe_orders"' in routes
    assert "restaurantCafeModeButton" in qss
    assert '(307, "CAFE_MODE_FOUNDATION")' in gate
    assert "tests/test_phase307_cafe_mode_foundation.py" in gate
