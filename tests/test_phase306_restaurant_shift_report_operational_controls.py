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
            self.path = tmp_path / "restaurant_shift_report.sqlite3"
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
    spec = importlib.util.spec_from_file_location("phase306_local_restaurant_gateway", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module.LocalRestaurantGateway()


def test_phase306_pure_shift_report_contract():
    from alrajhi_client.features.restaurant.restaurant_shift_report import (
        build_operational_controls,
        required_shift_report_sections,
        shift_close_blocker_keys,
        shift_report_blockers,
        shift_report_can_close,
    )

    assert required_shift_report_sections() == (
        "period",
        "summary",
        "payment_methods",
        "open_sessions",
        "top_items",
        "operational_controls",
    )
    assert "queued_print_jobs" in shift_close_blocker_keys()
    blocked = {"operational_controls": build_operational_controls(open_sessions=1, unpaid_open_sessions=1, active_kitchen_tickets=0, queued_print_jobs=0)}
    assert shift_report_can_close(blocked) is False
    assert shift_report_blockers(blocked) == ("open_sessions", "unpaid_open_sessions")
    ready = {"operational_controls": build_operational_controls(open_sessions=0, unpaid_open_sessions=0, active_kitchen_tickets=0, queued_print_jobs=0)}
    assert shift_report_can_close(ready) is True


def test_local_gateway_shift_report_blocks_then_allows_close(monkeypatch, tmp_path):
    gateway = _load_gateway(monkeypatch, tmp_path)
    table = gateway.list_tables()[0]
    session = gateway.open_table(table["id"], guests=2, waiter_id="waiter-1")
    gateway.add_order_line(session["id"], item_name="Coffee", quantity="2", unit_price="3.50")
    sent = gateway.send_to_kitchen(session["id"])
    job = gateway.queue_ticket_print(sent["ticket"]["id"], job_type="kot")

    blocked = gateway.restaurant_shift_report()
    assert blocked["summary"]["open_sessions"] == 1
    assert blocked["summary"]["unpaid_open_balance"] == "7.00"
    assert blocked["operational_controls"]["can_close_shift"] is False
    assert set(blocked["operational_controls"]["blockers"]) >= {"open_sessions", "unpaid_open_sessions", "active_kitchen_tickets", "queued_print_jobs"}
    assert blocked["open_sessions"][0]["remaining"] == "7.00"

    gateway.mark_print_job_done(job["job_id"])
    gateway.update_kitchen_ticket_status(sent["ticket"]["id"], "served")
    gateway.record_payment(session["id"], amount="2.00", payment_method="cash")
    gateway.record_payment(session["id"], amount="5.00", payment_method="card")
    closed = gateway.checkout_session(session["id"], paid_amount="0", payment_method="mixed")
    assert closed["status"] == "closed"

    report = gateway.restaurant_shift_report()
    assert report["summary"]["total_sessions"] == 1
    assert report["summary"]["closed_sessions"] == 1
    assert report["summary"]["open_sessions"] == 0
    assert report["summary"]["payments_total"] == "7.00"
    assert report["summary"]["cash_total"] == "2.00"
    assert report["summary"]["card_total"] == "5.00"
    assert report["payment_methods"] == {"card": "5.00", "cash": "2.00"}
    assert report["top_items"][0]["item_name"] == "Coffee"
    assert report["operational_controls"]["can_close_shift"] is True
    assert report["operational_controls"]["blockers"] == []


def test_phase306_gateway_service_route_ui_and_release_gate_contracts():
    abstract_gateway = (ROOT / "alrajhi_client" / "gateways" / "restaurant_gateway.py").read_text(encoding="utf-8")
    remote_gateway = (ROOT / "alrajhi_client" / "gateways" / "remote" / "restaurant_gateway.py").read_text(encoding="utf-8")
    service = (ROOT / "alrajhi_client" / "core" / "services" / "restaurant_service.py").read_text(encoding="utf-8")
    routes = (ROOT / "alrajhi_server" / "services" / "http_routes" / "restaurant.py").read_text(encoding="utf-8")
    widget = (ROOT / "alrajhi_client" / "views" / "restaurant" / "restaurant_analytics_widget.py").read_text(encoding="utf-8")
    translator = (ROOT / "alrajhi_client" / "i18n" / "translator.py").read_text(encoding="utf-8")
    gate = (ROOT / "alrajhi_client" / "workspace" / "quality" / "release_gate_contract.py").read_text(encoding="utf-8")

    assert "def restaurant_shift_report" in abstract_gateway
    assert "/api/restaurant/shift_report" in remote_gateway
    assert "restaurant_service.restaurant_shift_report" in service
    assert '@restaurant_bp.route("/restaurant/shift_report"' in routes
    assert "service.restaurant_shift_report" in widget
    assert "restaurant.analytics.shift_close_status" in translator
    assert '(306, "RESTAURANT_SHIFT_REPORT_OPERATIONAL_CONTROLS")' in gate
    assert "tests/test_phase306_restaurant_shift_report_operational_controls.py" in gate
