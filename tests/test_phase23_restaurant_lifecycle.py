import importlib.util
import sqlite3
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load_gateway(monkeypatch, tmp_path):
    class TempDatabaseConnection:
        def __init__(self):
            self.path = tmp_path / "restaurant_lifecycle.sqlite3"
            self.conn = sqlite3.connect(self.path)
            self.conn.row_factory = sqlite3.Row
            self.conn.execute("PRAGMA foreign_keys=ON")

        def get_connection(self):
            return self.conn

    database_pkg = types.ModuleType("database")
    connection_mod = types.ModuleType("database.connection")
    connection_mod.DatabaseConnection = TempDatabaseConnection
    gateways_pkg = types.ModuleType("gateways")
    restaurant_gateway_mod = types.ModuleType("gateways.restaurant_gateway")
    restaurant_gateway_mod.RestaurantGateway = object

    monkeypatch.setitem(sys.modules, "database", database_pkg)
    monkeypatch.setitem(sys.modules, "database.connection", connection_mod)
    monkeypatch.setitem(sys.modules, "gateways", gateways_pkg)
    monkeypatch.setitem(sys.modules, "gateways.restaurant_gateway", restaurant_gateway_mod)

    path = ROOT / "alrajhi_client" / "gateways" / "local" / "restaurant_gateway.py"
    spec = importlib.util.spec_from_file_location("phase23_local_restaurant_gateway", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module.LocalRestaurantGateway()


def test_restaurant_lifecycle_blocks_payment_and_close_until_new_lines_are_sent(monkeypatch, tmp_path):
    gateway = _load_gateway(monkeypatch, tmp_path)
    table = gateway.list_tables()[0]
    session = gateway.open_table(table["id"], guests=3)
    line = gateway.add_order_line(session["id"], item_name="Soup", quantity="2", unit_price="5")
    assert line["kitchen_status"] == "new"

    for action in (gateway.mark_payment_pending, gateway.close_session):
        try:
            action(session["id"])
        except ValueError as exc:
            assert "new" in str(exc).lower() or "kitchen" in str(exc).lower()
        else:
            raise AssertionError("New kitchen lines must block payment and close workflows")

    ticket = gateway.send_to_kitchen(session["id"])
    assert ticket["ticket"]
    sent_session = gateway.get_session(session["id"])
    assert sent_session["lines"][0]["kitchen_status"] == "sent"

    payment = gateway.mark_payment_pending(session["id"])
    assert payment["payment_pending"] is True
    tables = gateway.list_tables()
    assert next(t for t in tables if t["id"] == table["id"])["status"] == "payment"

    closed = gateway.close_session(session["id"])
    assert closed["status"] == "closed"
    tables = gateway.list_tables()
    assert next(t for t in tables if t["id"] == table["id"])["status"] == "free"


def test_restaurant_line_status_validation(monkeypatch, tmp_path):
    gateway = _load_gateway(monkeypatch, tmp_path)
    table = gateway.list_tables()[0]
    session = gateway.open_table(table["id"])
    line = gateway.add_order_line(session["id"], item_name="Coffee")

    updated = gateway.update_line_status(line["id"], "preparing")
    assert updated["kitchen_status"] == "preparing"

    try:
        gateway.update_line_status(line["id"], "not-a-status")
    except ValueError as exc:
        assert "invalid" in str(exc).lower()
    else:
        raise AssertionError("Invalid kitchen status must be rejected")


def test_phase23_translation_keys_exist_for_all_languages():
    from alrajhi_client.i18n import translator

    keys = [
        "restaurant.mark_payment_pending",
        "restaurant.payment_pending",
        "restaurant.line_status.preparing",
        "restaurant.line_status.served",
    ]
    for lang in ("ar", "de", "en"):
        translator.set_language(lang)
        for key in keys:
            assert translator.translate(key) != key
