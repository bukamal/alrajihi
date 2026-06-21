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
            self.path = tmp_path / "cafe_phase309.sqlite3"
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
    spec = importlib.util.spec_from_file_location("phase309_local_restaurant_gateway", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module.LocalRestaurantGateway()


def test_phase309_barista_ticket_filter_keeps_cafe_and_restaurant_separate(monkeypatch, tmp_path):
    gateway = _load_gateway(monkeypatch, tmp_path)

    table = gateway.list_tables()[0]
    dine_in = gateway.open_table(table["id"], guests=2)
    gateway.add_order_line(dine_in["id"], item_name="Burger", quantity="1", unit_price="10")
    gateway.send_to_kitchen(dine_in["id"])

    cafe = gateway.create_cafe_quick_order(customer_name="Walk-in", notes="cafe")
    gateway.add_order_line(cafe["id"], item_name="Latte", quantity="1", unit_price="4")
    gateway.send_to_kitchen(cafe["id"])

    all_tickets = gateway.list_kitchen_tickets(status="all", limit=20)
    cafe_tickets = gateway.list_kitchen_tickets(status="all", limit=20, order_type="cafe_quick_order")
    restaurant_tickets = gateway.list_kitchen_tickets(status="all", limit=20, order_type="dine_in")

    assert len(all_tickets) >= 2
    assert cafe_tickets and all(row.get("order_type") == "cafe_quick_order" for row in cafe_tickets)
    assert restaurant_tickets and all(row.get("order_type") == "dine_in" for row in restaurant_tickets)
    assert {row["id"] for row in cafe_tickets}.isdisjoint({row["id"] for row in restaurant_tickets})


def test_phase309_cafe_workspace_shell_contracts_are_registered():
    dashboard = (ROOT / "alrajhi_client" / "views" / "restaurant" / "restaurant_dashboard.py").read_text(encoding="utf-8")
    pos = (ROOT / "alrajhi_client" / "views" / "restaurant" / "restaurant_pos_widget.py").read_text(encoding="utf-8")
    kds = (ROOT / "alrajhi_client" / "views" / "restaurant" / "kitchen_display_widget.py").read_text(encoding="utf-8")
    service = (ROOT / "alrajhi_client" / "core" / "services" / "restaurant_service.py").read_text(encoding="utf-8")
    abstract_gateway = (ROOT / "alrajhi_client" / "gateways" / "restaurant_gateway.py").read_text(encoding="utf-8")
    local_gateway = (ROOT / "alrajhi_client" / "gateways" / "local" / "restaurant_gateway.py").read_text(encoding="utf-8")
    remote_gateway = (ROOT / "alrajhi_client" / "gateways" / "remote" / "restaurant_gateway.py").read_text(encoding="utf-8")
    server_repo = (ROOT / "alrajhi_server" / "repositories" / "restaurant_repository.py").read_text(encoding="utf-8")
    routes = (ROOT / "alrajhi_server" / "services" / "http_routes" / "restaurant.py").read_text(encoding="utf-8")
    qss = (ROOT / "alrajhi_client" / "theme" / "qss.py").read_text(encoding="utf-8")
    i18n = (ROOT / "alrajhi_client" / "i18n" / "translator.py").read_text(encoding="utf-8")
    gate = (ROOT / "alrajhi_client" / "workspace" / "quality" / "release_gate_contract.py").read_text(encoding="utf-8")

    assert "restaurantCafeWorkspaceShell" in dashboard
    assert "start_new_cafe_order" in dashboard
    assert "show_cafe_preparation_mode" in dashboard
    assert "show_cafe_report_mode" in dashboard
    assert "restaurant_operator_mode" in dashboard
    assert "set_cafe_workspace_mode" in pos
    assert "restaurant.cafe_send_to_barista" in pos
    assert "restaurant_order_context" in pos
    assert "def set_cafe_context" in kds
    assert "restaurant_kds_context" in kds
    assert "order_type = \"cafe_quick_order\"" in kds
    assert "order_type: str | None = None" in service
    assert "order_type: str | None = None" in abstract_gateway
    assert "COALESCE(s.order_type, 'dine_in')=?" in local_gateway
    assert 'params["order_type"]' in remote_gateway
    assert "order_type=request.args.get(\"order_type\") or None" in routes
    assert "COALESCE(s.order_type, 'dine_in')=?" in server_repo
    assert "restaurantCafeWorkspaceShell" in qss
    assert "restaurant.cafe_workspace_title" in i18n
    assert '(309, "CAFE_WORKSPACE_SHELL")' in gate
    assert "tests/test_phase309_cafe_workspace_shell.py" in gate
