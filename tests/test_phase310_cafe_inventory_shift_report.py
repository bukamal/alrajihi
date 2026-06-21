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
            self.path = tmp_path / "cafe_phase310.sqlite3"
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
                    reorder_level TEXT DEFAULT '0',
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
                    created_at TEXT,
                    user_id TEXT,
                    movement_date TEXT
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
    spec = importlib.util.spec_from_file_location("phase310_local_restaurant_gateway", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module.LocalRestaurantGateway()


def test_phase310_cafe_shift_report_filters_orders_and_inventory(monkeypatch, tmp_path):
    gateway = _load_gateway(monkeypatch, tmp_path)
    conn = gateway._conn()
    conn.execute("INSERT INTO items(id, name, selling_price, unit, quantity, average_cost, reorder_level) VALUES (1, 'Latte', '5', 'cup', '100', '0', '0')")
    conn.execute("INSERT INTO items(id, name, selling_price, unit, quantity, average_cost, reorder_level) VALUES (2, 'Coffee Beans', '0', 'g', '4', '0.05', '10')")
    conn.commit()

    gateway.upsert_recipe(item_id=1, name="Latte recipe", yield_quantity="1", lines=[
        {"component_item_id": 2, "component_name": "Coffee Beans", "quantity": "2", "unit": "g", "unit_cost": "0.05"},
    ])

    cafe = gateway.create_cafe_quick_order(customer_name="Walk-in")
    line = gateway.add_order_line(cafe["id"], item_id=1, item_name="Latte", quantity="2", unit_price="5")
    gateway.add_order_line_modifier(line["id"], name="Large", action="size", price_delta="1", quantity="1", kitchen_label="Large")
    gateway.add_order_line_modifier(line["id"], name="Extra shot", action="add", price_delta="0.50", quantity="1", kitchen_label="Extra shot")
    gateway.send_to_kitchen(cafe["id"])
    gateway.update_kitchen_ticket_status(gateway.list_kitchen_tickets(status="all", order_type="cafe_quick_order")[0]["id"], "served")
    gateway.record_payment(cafe["id"], amount="11.50", payment_method="card", notes="barista")
    gateway.checkout_session(cafe["id"], paid_amount="0", payment_method="card")

    table = gateway.upsert_table(name="Dine In", zone="Main", seats=2)
    dine = gateway.open_table(table["id"], guests=1)
    gateway.add_order_line(dine["id"], item_name="Burger", quantity="1", unit_price="99")

    report = gateway.cafe_shift_report()
    assert report["period"]["order_type"] == "cafe_quick_order"
    assert report["summary"]["total_orders"] == 1
    assert report["summary"]["closed_orders"] == 1
    assert report["summary"]["payments_total"] == "11.50"
    assert report["payment_methods"]["card"] == "11.50"
    assert report["top_drinks"][0]["item_name"] == "Latte"
    assert {row["name"] for row in report["top_modifiers"]} >= {"Large", "Extra shot"}
    assert report["inventory_consumption"][0]["component_name"] == "Coffee Beans"
    assert report["low_stock_alerts"] and report["low_stock_alerts"][0]["name"] == "Coffee Beans"
    assert report["operational_controls"]["can_close_shift"] is True
    assert report["open_orders"] == []


def test_phase310_cafe_shift_report_blocks_open_cafe_orders(monkeypatch, tmp_path):
    gateway = _load_gateway(monkeypatch, tmp_path)
    cafe = gateway.create_cafe_quick_order(customer_name="Open")
    gateway.add_order_line(cafe["id"], item_name="Americano", quantity="1", unit_price="3")

    report = gateway.cafe_shift_report()
    assert report["summary"]["open_orders"] == 1
    assert "open_orders" in report["operational_controls"]["blockers"]
    assert report["operational_controls"]["can_close_shift"] is False


def test_phase310_cafe_report_contracts_are_registered():
    feature = (ROOT / "alrajhi_client" / "features" / "restaurant" / "cafe_shift_report.py").read_text(encoding="utf-8")
    service = (ROOT / "alrajhi_client" / "core" / "services" / "restaurant_service.py").read_text(encoding="utf-8")
    abstract_gateway = (ROOT / "alrajhi_client" / "gateways" / "restaurant_gateway.py").read_text(encoding="utf-8")
    local_gateway = (ROOT / "alrajhi_client" / "gateways" / "local" / "restaurant_gateway.py").read_text(encoding="utf-8")
    remote_gateway = (ROOT / "alrajhi_client" / "gateways" / "remote" / "restaurant_gateway.py").read_text(encoding="utf-8")
    server_repo = (ROOT / "alrajhi_server" / "repositories" / "restaurant_repository.py").read_text(encoding="utf-8")
    routes = (ROOT / "alrajhi_server" / "services" / "http_routes" / "restaurant.py").read_text(encoding="utf-8")
    analytics = (ROOT / "alrajhi_client" / "views" / "restaurant" / "restaurant_analytics_widget.py").read_text(encoding="utf-8")
    dashboard = (ROOT / "alrajhi_client" / "views" / "restaurant" / "restaurant_dashboard.py").read_text(encoding="utf-8")
    i18n = (ROOT / "alrajhi_client" / "i18n" / "translator.py").read_text(encoding="utf-8")
    gate = (ROOT / "alrajhi_client" / "workspace" / "quality" / "release_gate_contract.py").read_text(encoding="utf-8")

    assert "CAFE_SHIFT_REPORT_REQUIRED_SECTIONS" in feature
    assert "def cafe_shift_report" in service
    assert "def cafe_shift_report" in abstract_gateway
    assert "def cafe_shift_report" in local_gateway
    assert "def cafe_shift_report" in remote_gateway
    assert "def cafe_shift_report" in server_repo
    assert "/restaurant/cafe_shift_report" in routes
    assert "service.cafe_shift_report" in analytics
    assert "set_cafe_context(True)" in dashboard
    assert "restaurant.cafe_shift_report_title" in i18n
    assert '(310, "cafe_inventory_shift_report")' in gate
    assert "tests/test_phase310_cafe_inventory_shift_report.py" in gate
