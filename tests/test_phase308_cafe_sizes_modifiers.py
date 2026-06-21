# -*- coding: utf-8 -*-
import importlib.util
import sqlite3
import sys
import types
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load_gateway(monkeypatch, tmp_path):
    class TempDatabaseConnection:
        def __init__(self):
            self.path = tmp_path / "cafe_phase308.sqlite3"
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
    spec = importlib.util.spec_from_file_location("phase308_local_restaurant_gateway", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module.LocalRestaurantGateway()


def test_phase308_cafe_size_and_addons_affect_total_and_kot_notes(monkeypatch, tmp_path):
    gateway = _load_gateway(monkeypatch, tmp_path)
    session = gateway.create_cafe_quick_order(customer_name="Walk-in", notes="cafe")
    line = gateway.add_order_line(session["id"], item_id=1, item_name="Latte", quantity="1", unit_price="4")
    size_group = gateway.upsert_modifier_group(item_id=1, name="Drink Size", max_selected=1, is_required=True)
    large = gateway.upsert_modifier_option(size_group["id"], name="Large", price_delta="1.25", kitchen_label="Large cup")
    addons = gateway.upsert_modifier_group(item_id=1, name="Add-ons", max_selected=5)
    vanilla = gateway.upsert_modifier_option(addons["id"], name="Vanilla", price_delta="0.50", kitchen_label="+ vanilla")

    gateway.add_order_line_modifier(line["id"], option_id=large["id"], action="size")
    gateway.add_order_line_modifier(line["id"], option_id=vanilla["id"], action="add")

    refreshed_session = gateway.get_session(session["id"])
    refreshed_line = refreshed_session["lines"][0]
    balance = gateway.session_balance(session["id"])

    assert refreshed_session["order_type"] == "cafe_quick_order"
    assert Decimal(refreshed_line["modifier_total"]) == Decimal("1.75")
    assert Decimal(refreshed_line["line_total"]) == Decimal("5.75")
    assert Decimal(balance["subtotal"]) == Decimal("5.75")
    assert "Large cup" in refreshed_line["kitchen_modifier_notes"]
    assert "+ vanilla" in refreshed_line["kitchen_modifier_notes"]

    gateway.send_to_kitchen(session["id"])
    kot_line = gateway._conn().execute("SELECT notes FROM kitchen_ticket_lines ORDER BY id DESC LIMIT 1").fetchone()
    assert "Large cup" in kot_line["notes"]
    assert "+ vanilla" in kot_line["notes"]


def test_phase308_cafe_policy_detects_size_group_and_normalizes_defaults():
    path = ROOT / "alrajhi_client" / "features" / "restaurant" / "cafe_size_modifier_policy.py"
    spec = importlib.util.spec_from_file_location("phase308_cafe_policy", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)

    size_group, addon_groups = module.split_size_and_modifier_groups([
        {"id": 1, "name": "حجم المشروب", "options": [{"id": 10, "name": "كبير", "price_delta": "2"}]},
        {"id": 2, "name": "Syrups", "options": []},
    ])
    assert size_group["id"] == 1
    assert addon_groups[0]["id"] == 2
    assert module.size_options_from_group(size_group)[0]["price_delta"] == "2"
    assert [row["code"] for row in module.default_size_options()] == ["small", "medium", "large"]
    mods = module.build_line_modifiers(size={"name": "Medium"}, modifiers=[{"name": "Extra shot", "price_delta": "0.75"}])
    assert mods[0]["action"] == "size"
    assert mods[1]["name"] == "Extra shot"


def test_phase308_cafe_ui_and_release_gate_contracts_are_registered():
    service = (ROOT / "alrajhi_client" / "core" / "services" / "restaurant_service.py").read_text(encoding="utf-8")
    pos = (ROOT / "alrajhi_client" / "views" / "restaurant" / "restaurant_pos_widget.py").read_text(encoding="utf-8")
    policy = (ROOT / "alrajhi_client" / "features" / "restaurant" / "cafe_size_modifier_policy.py").read_text(encoding="utf-8")
    qss = (ROOT / "alrajhi_client" / "theme" / "qss.py").read_text(encoding="utf-8")
    i18n = (ROOT / "alrajhi_client" / "i18n" / "translator.py").read_text(encoding="utf-8")
    gate = (ROOT / "alrajhi_client" / "workspace" / "quality" / "release_gate_contract.py").read_text(encoding="utf-8")

    assert "def add_cafe_line" in service
    assert "build_line_modifiers" in service
    assert "class CafeItemOptionsDialog" in pos
    assert "CafeItemOptionsDialog(item=item" in pos
    assert "is_cafe_order(self.session)" in pos
    assert "SIZE_ACTION" in policy and "DEFAULT_CAFE_SIZES" in policy
    assert "restaurantCafeSizeCombo" in qss
    assert "restaurant.cafe_size.large" in i18n
    assert '(308, "CAFE_SIZES_MODIFIERS")' in gate
    assert "tests/test_phase308_cafe_sizes_modifiers.py" in gate
