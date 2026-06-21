import datetime
import importlib.util
import sqlite3
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load_gateway(monkeypatch, tmp_path):
    class TempDatabaseConnection:
        def __init__(self):
            self.path = tmp_path / "restaurant_kds_phase288.sqlite3"
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
    spec = importlib.util.spec_from_file_location("phase288_local_restaurant_gateway", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module.LocalRestaurantGateway()


def test_kds_active_filter_priority_overdue_and_state_timestamps(monkeypatch, tmp_path):
    gateway = _load_gateway(monkeypatch, tmp_path)
    table = gateway.list_tables()[0]
    session = gateway.open_table(table["id"])
    gateway.add_order_line(session["id"], item_name="Steak", quantity="1", unit_price="20")
    sent = gateway.send_to_kitchen(session["id"])
    ticket_id = sent["ticket"]["id"]

    old_time = (datetime.datetime.now() - datetime.timedelta(minutes=30)).isoformat(timespec="seconds")
    gateway._conn().execute("UPDATE kitchen_tickets SET sent_at=?, priority=5 WHERE id=?", (old_time, ticket_id))
    gateway._conn().commit()

    active = gateway.list_kitchen_tickets(status="active")
    assert active[0]["id"] == ticket_id
    assert active[0]["is_overdue"] is True
    assert active[0]["elapsed_minutes"] >= 29
    assert active[0]["display_bucket"] == "active"

    preparing = gateway.update_kitchen_ticket_status(ticket_id, "preparing")
    assert preparing["status"] == "preparing"
    assert preparing.get("preparing_at")

    ready = gateway.update_kitchen_ticket_status(ticket_id, "ready")
    assert ready["status"] == "ready"
    assert ready.get("ready_at")

    served = gateway.update_kitchen_ticket_status(ticket_id, "served")
    assert served["status"] == "served"
    assert served.get("served_at")
    assert not any(ticket["id"] == ticket_id for ticket in gateway.list_kitchen_tickets(status="active"))
    assert any(ticket["id"] == ticket_id for ticket in gateway.list_kitchen_tickets(status="all"))


def test_kitchen_display_hardening_contract_is_present():
    helper = (ROOT / "alrajhi_client" / "features" / "restaurant" / "kitchen_display_state.py").read_text(encoding="utf-8")
    local = (ROOT / "alrajhi_client" / "gateways" / "local" / "restaurant_gateway.py").read_text(encoding="utf-8")
    server = (ROOT / "alrajhi_server" / "repositories" / "restaurant_repository.py").read_text(encoding="utf-8")
    kds = (ROOT / "alrajhi_client" / "views" / "restaurant" / "kitchen_display_widget.py").read_text(encoding="utf-8")
    translations = (ROOT / "alrajhi_client" / "i18n" / "translator.py").read_text(encoding="utf-8")
    qss = (ROOT / "alrajhi_client" / "theme" / "qss.py").read_text(encoding="utf-8")
    release_gate = (ROOT / "alrajhi_client" / "workspace" / "quality" / "release_gate_contract.py").read_text(encoding="utf-8")

    assert "ACTIVE_KITCHEN_STATUSES" in helper
    assert "sort_kitchen_tickets" in helper
    assert "preparing_at" in local and "ready_at" in local and "served_at" in local
    assert "_sort_restaurant_kitchen_tickets" in server
    assert "restaurantKDSStatusFilter" in kds
    assert "restaurantKDSCounterBar" in kds
    assert "restaurant.kds.overdue" in translations
    assert "restaurantKDSDetailMeta" in qss
    assert "restaurant_kds_hardening" in release_gate
