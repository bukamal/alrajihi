import importlib.util
import sqlite3
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load_local_restaurant_gateway(monkeypatch, tmp_path):
    class TempDatabaseConnection:
        def __init__(self):
            self.path = tmp_path / "restaurant_fk.sqlite3"
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
    spec = importlib.util.spec_from_file_location("phase22_local_restaurant_gateway", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module.LocalRestaurantGateway()


def test_local_restaurant_first_click_seeds_real_tables_and_opens_session(monkeypatch, tmp_path):
    gateway = _load_local_restaurant_gateway(monkeypatch, tmp_path)

    tables = gateway.list_tables()
    assert len(tables) == 12
    assert tables[0]["id"] is not None

    session = gateway.open_table(tables[0]["id"], guests=2)
    assert session["table_id"] == tables[0]["id"]
    assert session["guests"] == 2


def test_local_restaurant_rejects_missing_table_before_session_insert(monkeypatch, tmp_path):
    gateway = _load_local_restaurant_gateway(monkeypatch, tmp_path)
    gateway._ensure_schema()

    try:
        gateway.open_table(9999, guests=1)
    except ValueError as exc:
        assert "refresh the table map" in str(exc)
    else:
        raise AssertionError("Expected missing restaurant table to be rejected before FK insert")
