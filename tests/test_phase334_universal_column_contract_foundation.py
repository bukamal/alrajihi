# -*- coding: utf-8 -*-
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
CLIENT = ROOT / "alrajhi_client"
if str(CLIENT) not in sys.path:
    sys.path.insert(0, str(CLIENT))


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_phase334_column_contract_types_are_pyqt_free_and_scoped():
    from workspace.tables import ColumnDefinition, TableColumnContract, validate_unique_keys

    col = ColumnDefinition("barcode", "transaction_column_barcode", settings_key="").scoped("ui/columns/items/materials")
    assert col.settings_key == "ui/columns/items/materials/barcode"
    contract = TableColumnContract("items", "materials", "read_only_list", "ui/columns/items/materials", (col,))
    assert contract.contract_id == "items.materials"
    assert contract.default_visible_keys() == ("barcode",)
    assert contract.default_printable_keys() == ("barcode",)
    assert contract.default_exportable_keys() == ("barcode",)
    assert validate_unique_keys(contract.columns) is True


def test_phase334_registry_defines_invoice_and_apparel_column_contracts():
    from workspace.tables import table_column_contract, contract_ids

    required = {"sales_invoices.lines", "purchase_invoices.lines", "returns.lines", "purchase_returns.lines", "apparel.variants", "apparel.reports"}
    assert required.issubset(set(contract_ids()))

    sales = table_column_contract("sales_invoices", "lines")
    purchase = table_column_contract("purchase_invoices", "lines")
    apparel = table_column_contract("apparel", "variants")
    assert sales and purchase and apparel
    assert {"row", "item", "qty", "price", "total"}.issubset({c.key for c in sales.columns})
    assert {"row", "item", "qty", "cost", "total"}.issubset({c.key for c in purchase.columns})
    assert {"item", "color", "size", "sku", "barcode", "quantity", "sale_price"}.issubset({c.key for c in apparel.columns})
    assert all(c.settings_key.startswith(f"{sales.settings_prefix}/") for c in sales.columns)
    assert sales.column("price").data_type == "money"
    assert purchase.column("cost").data_type == "money"
    assert apparel.column("barcode").data_type == "barcode"
    assert apparel.column("status").printable_default is False


def test_phase334_transaction_schema_bridges_to_universal_contracts():
    schema = read("alrajhi_client/features/transactions/grids/transaction_column_schema.py")
    assert "from workspace.tables import ColumnDefinition, table_column_contract" in schema
    assert "def to_column_definition" in schema
    assert "def universal_contract_for_document" in schema
    assert "def universal_columns_for_document" in schema
    assert '"purchase_invoice": ("purchase_invoices", "lines")' in schema
    assert '"sales_invoice": ("sales_invoices", "lines")' in schema
    assert 'return "money"' in schema


def test_phase334_tables_can_attach_contracts_and_print_export_use_contract_flags():
    custom = read("alrajhi_client/views/custom_table_view.py")
    trx = read("alrajhi_client/features/transactions/transaction_document_tab.py")
    apparel = read("alrajhi_client/views/apparel/apparel_workspace_widget.py")
    assert "def set_column_contract" in custom
    assert "def _columns_for_purpose" in custom
    assert "self._columns_for_purpose('export')" in custom
    assert "self._columns_for_purpose('print')" in custom
    assert "self.grid.set_column_contract(*page_table)" in trx
    assert "self.table.set_column_contract(\"apparel\", \"variants\")" in apparel


def test_phase334_release_gate_registered_and_documented():
    gate = read("alrajhi_client/workspace/quality/release_gate_contract.py")
    assert '(334, "UNIVERSAL_COLUMN_CONTRACT_FOUNDATION")' in gate
    assert "tests/test_phase334_universal_column_contract_foundation.py" in gate
    assert 'ReleaseGateCheck("universal_column_contract_foundation"' in gate
    assert (ROOT / "PHASE334_UNIVERSAL_COLUMN_CONTRACT_FOUNDATION.md").exists()
