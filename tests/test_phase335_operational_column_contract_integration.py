# -*- coding: utf-8 -*-
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"
if str(CLIENT) not in sys.path:
    sys.path.insert(0, str(CLIENT))


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_phase335_operational_contracts_are_registered():
    from workspace.tables import contract_ids, table_column_contract

    required = {
        "pos.lines",
        "restaurant.order_lines",
        "restaurant.kds_tickets",
        "restaurant.kds_lines",
        "cafe.order_lines",
        "cafe.preparation_tickets",
        "cafe.preparation_lines",
        "apparel.variants",
        "apparel.reports",
    }
    assert required.issubset(set(contract_ids()))

    pos = table_column_contract("pos", "lines")
    restaurant = table_column_contract("restaurant", "order_lines")
    cafe = table_column_contract("cafe", "order_lines")
    assert pos and restaurant and cafe
    assert {"row", "barcode", "item", "qty", "price", "total"}.issubset({c.key for c in pos.columns})
    assert {"row", "item", "qty", "price", "total", "status"}.issubset({c.key for c in restaurant.columns})
    assert cafe.column("modifiers").visible_default is True
    assert cafe.column("notes").printable_default is True
    assert restaurant.column("modifiers").visible_default is False
    assert all(c.settings_key.startswith("ui/columns/pos/lines/") for c in pos.columns)


def test_phase335_pos_and_restaurant_schemas_consume_universal_contracts():
    pos_schema = read("alrajhi_client/features/pos/pos_line_schema.py")
    restaurant_schema = read("alrajhi_client/features/restaurant/restaurant_order_schema.py")
    adapter = read("alrajhi_client/features/transactions/grids/universal_column_adapter.py")

    assert "transaction_columns_from_contract(\"pos\", \"lines\"" in pos_schema
    assert "transaction_columns_from_contract(\"restaurant\", \"order_lines\"" in restaurant_schema
    assert "def cafe_order_schema" in restaurant_schema
    assert "transaction_columns_from_contract(\"cafe\", \"order_lines\"" in restaurant_schema
    assert "def transaction_column_from_definition" in adapter
    assert "printable_default=bool(column.printable_default)" in adapter
    assert "exportable_default=bool(column.exportable_default)" in adapter


def test_phase335_operational_grids_attach_column_contracts():
    pos_grid = read("alrajhi_client/features/pos/pos_line_grid.py")
    restaurant_grid = read("alrajhi_client/features/restaurant/restaurant_order_grid.py")
    restaurant_pos = read("alrajhi_client/views/restaurant/restaurant_pos_widget.py")
    kds = read("alrajhi_client/views/restaurant/kitchen_display_widget.py")

    assert "self.set_column_contract(\"pos\", \"lines\")" in pos_grid
    assert "self.set_column_contract(\"restaurant\", \"order_lines\")" in restaurant_grid
    assert "self.lines.set_column_contract(\"restaurant\", \"order_lines\")" in restaurant_pos
    assert "self.order_model.set_order_context(page_id)" in restaurant_pos
    assert "self.lines.set_column_contract(page_id, \"order_lines\")" in restaurant_pos
    assert '"restaurant.kds_tickets"' in kds
    assert '"cafe.preparation_tickets"' in kds


def test_phase335_apparel_report_uses_report_contract():
    apparel = read("alrajhi_client/views/apparel/apparel_workspace_widget.py")
    assert "from workspace.tables import table_column_contract" in apparel
    assert "self.report_table.setProperty(\"column_contract_id\", \"apparel.reports\")" in apparel
    assert "contract = table_column_contract(\"apparel\", \"reports\")" in apparel
    assert "headers = [translate(column.label_key) for column in columns]" in apparel
    assert "keys = [column.key for column in columns]" in apparel


def test_phase335_release_gate_registered_and_documented():
    gate = read("alrajhi_client/workspace/quality/release_gate_contract.py")
    assert '(335, "OPERATIONAL_COLUMN_CONTRACT_INTEGRATION")' in gate
    assert '(335, "operational_column_contract_integration")' in gate
    assert "tests/test_phase335_operational_column_contract_integration.py" in gate
    assert 'ReleaseGateCheck("operational_column_contract_integration"' in gate
    assert (ROOT / "PHASE335_OPERATIONAL_COLUMN_CONTRACT_INTEGRATION.md").exists()
