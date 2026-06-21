import importlib.util
import sqlite3
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load_gateway(monkeypatch, tmp_path):
    class TempDatabaseConnection:
        def __init__(self):
            self.path = tmp_path / "restaurant_phase293.sqlite3"
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
    spec = importlib.util.spec_from_file_location("phase293_local_restaurant_gateway", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module.LocalRestaurantGateway()


def test_reservation_is_visible_and_seated_when_opened(monkeypatch, tmp_path):
    gateway = _load_gateway(monkeypatch, tmp_path)
    tables = gateway.list_tables()
    reservation = gateway.reserve_table(tables[0]["id"], customer_name="Family", phone="555", guests=4)
    listed = {row["id"]: row for row in gateway.list_tables()}
    table = listed[tables[0]["id"]]

    assert table["ui_status"] == "reserved"
    assert table["active_reservation_id"] == reservation["id"]
    assert table["active_reservation_customer"] == "Family"
    assert table["active_reservation_guests"] == 4

    session = gateway.open_table(tables[0]["id"], guests=4)
    seated = gateway._conn().execute("SELECT status, seated_at FROM restaurant_reservations WHERE id=?", (reservation["id"],)).fetchone()
    assert seated["status"] == "seated"
    assert seated["seated_at"]
    assert session["table_id"] == tables[0]["id"]

    operations = [row["operation"] for row in gateway._conn().execute("SELECT operation FROM restaurant_table_operations ORDER BY id").fetchall()]
    assert "reserve_table" in operations
    assert "seat_reservation" in operations
    assert "open_table" in operations


def test_transfer_split_and_merge_record_table_operations(monkeypatch, tmp_path):
    gateway = _load_gateway(monkeypatch, tmp_path)
    tables = gateway.list_tables()
    source = gateway.open_table(tables[0]["id"], guests=2)
    target = gateway.open_table(tables[2]["id"], guests=1)
    line_a = gateway.add_order_line(source["id"], item_name="Soup", quantity="1", unit_price="4")
    line_b = gateway.add_order_line(source["id"], item_name="Steak", quantity="1", unit_price="15")

    gateway.reserve_table(tables[1]["id"], customer_name="Target", guests=2)
    transferred = gateway.transfer_session(source["id"], tables[1]["id"])
    assert transferred["table_id"] == tables[1]["id"]
    assert gateway._conn().execute("SELECT status FROM restaurant_reservations WHERE table_id=?", (tables[1]["id"],)).fetchone()["status"] == "seated"

    split = gateway.split_lines_to_table(transferred["id"], [line_b["id"]], tables[3]["id"])
    assert split["moved_line_ids"] == [line_b["id"]]
    merged = gateway.merge_sessions(target["id"], transferred["id"])
    assert merged["merged_source_session_id"] == target["id"]

    operations = [row["operation"] for row in gateway._conn().execute("SELECT operation FROM restaurant_table_operations ORDER BY id").fetchall()]
    assert "transfer_session" in operations
    assert "split_lines_to_table" in operations
    assert "merge_sessions" in operations


def test_phase293_ui_and_contract_surface_present():
    dashboard = (ROOT / "alrajhi_client" / "views" / "restaurant" / "restaurant_dashboard.py").read_text(encoding="utf-8")
    local = (ROOT / "alrajhi_client" / "gateways" / "local" / "restaurant_gateway.py").read_text(encoding="utf-8")
    server = (ROOT / "alrajhi_server" / "repositories" / "restaurant_repository.py").read_text(encoding="utf-8")
    qss = (ROOT / "alrajhi_client" / "theme" / "qss.py").read_text(encoding="utf-8")
    i18n = (ROOT / "alrajhi_client" / "i18n" / "translator.py").read_text(encoding="utf-8")

    for token in (
        "RestaurantReservationDialog",
        "RestaurantTableTargetDialog",
        "reserve_table_btn",
        "transfer_table_btn",
        "merge_table_btn",
        "move_line_btn",
        "restaurantTableOperationsBar",
    ):
        assert token in dashboard
    for token in ("restaurant_table_operations", "_record_table_operation", "_seat_reserved_table_if_needed", "active_reservation_customer"):
        assert token in local
        assert token in server
    assert "restaurantTableOperationButton" in qss
    assert "restaurant.table_operations" in i18n
